import sys

import tqdm
import numpy as np
from scipy.spatial import KDTree

from mumott.methods.basis_sets.base_basis_set import BasisSet


class Simulator:
    """ Simulator for tensor tomography samples based on a geometry and a few
    sources with associated influence functions.
    Designed primarily for local representations. Polynomial representations,
    such as spherical harmonics, may require other residual functions which take
    the different frequency bands into account.

    Parameters
    ----------
    volume_mask : np.ndarray[int]
        A three-dimensional mask. The shape of the mask defines the shape of the entire
        simulated volume.
        The non-zero entries of the mask determine where the simulated sample is
        located. The non-zero entries should be mostly contiguous for good results.
    basis_set : BasisSet
        The basis set used for the simulation. Ideally local representations such as
        :class:`GaussianKernels <mumott.methods.basis_sets.GaussianKernels>`
        should be used.
        Do not modify the basis set after creating the simulator.
    seed : int
        Seed for the random number generator. Useful for generating consistent
        simulations. By default no seed is used.
    distance_radius : float
        Radius for the balls used in determining interior distances.
        Usually, this value should not be changed, but it can be increased
        to take larger strides in the interior of the sample.
        Default value is ``np.sqrt(2) * 1.01``.
    """
    def __init__(self,
                 volume_mask: np.ndarray[int],
                 basis_set: BasisSet,
                 seed: int = None,
                 distance_radius: float = np.sqrt(2) * 1.01) -> None:
        self._volume_mask = volume_mask > 0
        self._basis_set = basis_set
        self._basis_set_hash = hash(basis_set)
        x, y, z = (np.arange(self.shape[0]),
                   np.arange(self.shape[1]),
                   np.arange(self.shape[2]))
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        # set X-coordinates of non-considered points to be impossibly large
        X[~self._volume_mask] = np.prod(self.shape)
        self._positions = np.concatenate((X.reshape(-1, 1), Y.reshape(-1, 1), Z.reshape(-1, 1)), axis=1)
        self._tree = KDTree(self._positions)
        self._source_locations = []
        self._source_distances = []
        self._source_exponents = []
        self._source_scale_parameters = []
        self._source_coefficients = []
        self._simulation = np.zeros(self.shape + (len(self._basis_set),), dtype=float)
        self._source_weights = np.ones(self.shape, dtype=float)
        self._rng = np.random.default_rng(seed)
        self._distance_radius = distance_radius

    def add_source(self,
                   location: tuple[int, int, int] = None,
                   coefficients: np.ndarray[float] = None,
                   influence_exponent: float = 2,
                   influence_scale_parameter: float = 10) -> None:
        """
        Add a source to your simulation.

        Parameters
        ----------
        location
            Location, in terms of indices, of the source.
            If not given, will be randomized weighted by inverse of distance
            to other source points.
        coefficients
            Coefficients defining the source. If not given, will be
            randomized in the interval ``[0, 1]``.
        influence_exponent
            Exponent of the influence of the influence of the source.
            Default value is ``2``, giving a Gaussian.
        influence_scale_parameter
            Scale parameter of the influence of the influence of the source.
            Default value is ``10``.

        Notes
        -----
        The equation for the source influence is ``np.exp(-(d / (p * s)) ** p)``,
        where ``d`` is the interior distance, ``s`` is the scale parameter,
        and ``p`` is the exponent.

        If a location is not given, a location will be searched for for no more than
        1e6 iterations. For large and sparse samples, consider specifying locations
        manually.
        """
        if location is None:
            iterations = 0
            while True:
                location = tuple(self._rng.integers((0, 0, 0), self.shape))
                if self._volume_mask[location] and self._rng.random() < self._source_weights[location]:
                    break
                if iterations > 1e6:
                    raise RuntimeError('Maximum number of iterations exceeded.'
                                       ' Specify location manually instead.')
                iterations += 1
        elif not self._volume_mask[location]:
            raise ValueError('location must be inside the valid region of the volume mask!')
        self._source_locations.append(location)
        self._source_distances.append(self._get_distances_to_point(location))
        # weight likelihood of placing a source by rms of distances
        distance_sum = np.power(self._source_distances, 2).sum(0)
        self._source_weights = np.sqrt(distance_sum / distance_sum.max())
        if coefficients is None:
            coefficients = self._rng.random(len(self.basis_set))
        self._source_coefficients.append(coefficients)
        self._source_scale_parameters.append(influence_scale_parameter)
        self._source_exponents.append(influence_exponent)

    def _get_distances_to_point(self, point):
        """ Internal method for computing interior distances. """
        distances = np.zeros_like(self._volume_mask, dtype=np.float64) - 1
        # Compute distances based on ball around source point
        ball = self._tree.query_ball_point(
            self._positions[np.ravel_multi_index(point, self.shape)], r=self._distance_radius, p=2)
        distances[tuple(point)] = 0
        list_of_balls = []
        list_of_distances = []
        self._recursive_ball_dijkstra(
            ball,
            self._positions[np.ravel_multi_index(point, self.shape)],
            distances,
            list_of_balls,
            list_of_distances,
            total_distance=0,
            generation=0)
        distances[distances < 0] = np.prod(self.shape)
        return distances

    def _recursive_ball_dijkstra(self,
                                 ball,
                                 point: tuple,
                                 distances: np.ndarray[float],
                                 list_of_balls: list,
                                 list_of_distances: list,
                                 total_distance,
                                 generation: int = 1):
        """ Recursive function that uses a variant of Dijkstra's Algorithm
        to find the internal distances in the simulation volume. """
        for ind, i in enumerate(ball):
            # Ignore any already-computed distance
            if distances[np.unravel_index(i, self.shape)] != -1:
                continue
            else:
                # Add previously computed  distance from source to new starting point
                list_of_balls.append(i)
                new_distance = total_distance + np.sqrt(((self._positions[i] - point) ** 2).sum())
                list_of_distances.append(new_distance)
                distances[np.unravel_index(i, self.shape)] = new_distance
        # Only carry out recursion from lowest level with generation 0.
        while (generation == 0) and (len(list_of_balls) > 0):
            next_ind = np.argmin(list_of_distances)
            next_point = list_of_balls[next_ind]
            next_distance = list_of_distances[next_ind]
            del list_of_balls[next_ind], list_of_distances[next_ind]
            new_ball = self._tree.query_ball_point(self._positions[next_point], r=self._distance_radius, p=2)
            self._recursive_ball_dijkstra(
                new_ball,
                self._positions[next_point],
                distances,
                list_of_balls,
                list_of_distances,
                next_distance)

    def _get_power_factor(self,
                          power_factor_weights: np.ndarray[float] = None):
        """ Computes the residual norm, gradient and the squared residuals of the model
        implied by the source points and the current simulation."""
        if power_factor_weights is None:
            power_factor_weights = np.ones(self.shape, dtype=float)
            power_factor_weights[~self._volume_mask] = 0.
        source_coefficients = np.array(self._source_coefficients).reshape(-1, 1, 1, 1, len(self.basis_set))
        model = self._simulation.reshape((1,) + self._simulation.shape)
        # pseudo-power
        model_power = (model ** 2).sum(-1)
        source_power = (source_coefficients ** 2).sum(-1)
        # influences affect only importance
        differences = (model_power - source_power) * self.influences
        residuals = (differences ** 2).sum(0)
        gradient = (
            2 * model * (power_factor_weights[None] * self.influences * differences)[..., None]).sum(0)
        norm = 0.5 * (residuals * power_factor_weights).sum()
        return norm, gradient, residuals

    def _get_residuals(self,
                       residual_weights: np.ndarray[float] = None):
        """ Computes the residual norm, gradient and the squared residuals of the model
        implied by the source points and the current simulation."""
        if residual_weights is None:
            residual_weights = np.ones(self.shape, dtype=float)
            residual_weights[~self._volume_mask] = 0.
        source_coefficients = np.array(self._source_coefficients).reshape(-1, 1, 1, 1, len(self.basis_set))
        model = self._simulation.reshape((1,) + self._simulation.shape)
        # pseudo-covariance
        covariance = (model * source_coefficients).sum(-1)
        source_variance = (source_coefficients ** 2).sum(-1)
        # influences affect both importance and expected degree of similarity
        differences = (covariance - source_variance * self.influences) * self.influences
        residuals = (differences ** 2).sum(0)
        gradient = (
            source_coefficients * (residual_weights[None] * self.influences * differences)[..., None]).sum(0)
        norm = 0.5 * (residuals * residual_weights).sum()
        return norm, gradient, residuals

    def _get_squared_total_variation(self, tv_weights: np.ndarray[float] = None):
        """ Computes the norm, gradient and squared value of the
        squared total variation of the simulation."""
        if tv_weights is None:
            tv_weights = np.ones(self.shape, dtype=float)
            tv_weights[~self._volume_mask] = 0.
        sub_sim = self._simulation[1:-1, 1:-1, 1:-1]
        slices_1 = [np.s_[:-1, :, :], np.s_[:, :-1, :], np.s_[:, :, :-1]]
        slices_2 = [np.s_[1:, :, :], np.s_[:, 1:, :], np.s_[:, :, 1:]]
        value = np.zeros_like(self._simulation)
        # view into value
        sub_value = value[1:-1, 1:-1, 1:-1]
        gradient = np.zeros_like(self._simulation)
        # view into gradient
        sub_grad = gradient[1:-1, 1:-1, 1:-1]
        for s1, s2 in zip(slices_1, slices_2):
            difference = (sub_sim[s1] - sub_sim[s2])
            sub_value[s1] += difference ** 2
            sub_grad[s1] += difference
        value = value.sum(-1)
        value_norm = 0.5 * (value * tv_weights).sum()
        gradient = gradient * tv_weights[..., None]
        return value_norm, gradient, value

    def optimize(self,
                 step_size: float = 0.01,
                 iterations: int = 10,
                 weighting_iterations: int = 5,
                 momentum: float = 0.95,
                 tv_weight: float = 0.1,
                 tv_exponent: float = 1.,
                 tv_delta: float = 0.01,
                 residual_exponent: float = 1.,
                 residual_delta: float = 0.05,
                 power_weight: float = 0.01,
                 power_exponent: float = 1,
                 power_delta: float = 0.01,
                 lower_bound: float = 0.):
        """ Optimizer for carrying out the simulation. Can be called repeatedly.
        Uses iteratively reweighted least squares, with weights calculated based on
        the Euclidean norm over each voxel.

        Parameters
        ----------
        step_size
            Step size for gradient descent.
        iterations
            Number of iterations for each gradient descent solution.
        weighting_iterations
            Number of reweighting iterations.
        momentum
            Nesterov momentum term.
        tv_weight
            Weight for the total variation term.
        tv_exponent
            Exponent for the total variation reweighting.
            Default is 1, which will approach a Euclidean norm considered.
        tv_delta
            Huber-style cutoff for the total variation factor normalization.
        residual_exponent
            Exponent for the residual norm reweighting.
        residual_delta
            Huber-style cutoff for the residual normalization.
        power_weight
            Weight for the power term.
        power_exponent
            Exponent for the power term.
        power_delta
            Huber-style cutoff for the power normalization.
        lower_bound
            Lower bound for coefficients. Coefficients will be
            clipped at these bounds at every reweighting.
        """
        residual = np.ones(self.shape, dtype=float)
        tv_value = np.ones(self.shape, dtype=float)
        power_value = np.ones(self.shape, dtype=float)
        pbar = tqdm.trange(weighting_iterations, file=sys.stdout)

        for _ in range(weighting_iterations):
            total_gradient = np.zeros_like(self._simulation)
            residual_weights = np.ones(self.shape, dtype=float)
            residual_weights[~self._volume_mask] = 0.
            residual_weights[self._volume_mask] *= \
                residual[self._volume_mask].clip(residual_delta, None) ** ((residual_exponent - 2) / 2)
            tv_weights = np.ones(self.shape, dtype=float)
            tv_weights[~self._volume_mask] = 0.
            tv_weights[self._volume_mask] *= \
                tv_value[self._volume_mask].clip(tv_delta, None) ** ((tv_exponent - 2) / 2)
            power_weights = np.ones(self.shape, dtype=float)
            power_weights[~self._volume_mask] = 0.
            power_weights[self._volume_mask] *= \
                power_value[self._volume_mask].clip(power_delta, None) ** ((power_exponent - 2) / 2)

            for _ in range(iterations):
                _, residual_gradient, _ = self._get_residuals(residual_weights)
                _, tv_gradient, _ = self._get_squared_total_variation(tv_weights)
                _, power_gradient, _ = self._get_power_factor(power_weights)
                gradient = residual_gradient + tv_gradient * tv_weight + power_gradient * power_weight
                self._simulation -= gradient * step_size
                total_gradient += gradient
                total_gradient *= momentum
                self._simulation -= total_gradient * step_size

            res_norm, _, residual = self._get_residuals(residual_weights)
            tv_norm, _, tv_value = self._get_squared_total_variation(tv_weights)
            power_norm, _, power_value = self._get_power_factor(power_weights)
            lf = res_norm + tv_norm * tv_weight + power_norm * power_weight
            pbar.set_description(
                f'Loss: {lf:.2e} Resid: {res_norm:.2e} TV: {tv_norm:.2e} Pow: {power_norm:.2e}')
            pbar.update(1)
            self._simulation.clip(lower_bound, None, out=self._simulation)

    def reset_simulation(self) -> None:
        """Resets the simulation by setting all elements to 0."""
        self._simulation[...] = 0

    @property
    def volume_mask(self) -> np.ndarray[float]:
        """ Mask defining valid sample voxels within the sample.
        Read-only property; create a new simulation to modify. """
        return self._volume_mask.copy()

    @property
    def basis_set(self) -> BasisSet:
        """ Basis set defining the representation used in the sample.
        Read-only property; do not modify. """
        if hash(self._basis_set) != self._basis_set_hash:
            raise ValueError('Hash of basis set does not match! Please recreate simulator.')
        return self._basis_set

    @property
    def shape(self) -> tuple[int, int, int]:
        """ Shape of the simulation and volume mask. """
        return self._volume_mask.shape

    @property
    def simulation(self) -> np.ndarray[float]:
        """ The simulated sample. """
        return self._simulation

    @property
    def distance_radius(self) -> np.ndarray[float]:
        """ Distance for ball defining interior distances. """
        return self._distance_radius

    @property
    def sources(self) -> dict:
        """ Dictionary of source properties.
        They are given as arrays where the first index specifies
        the source, so that ``len(array)`` is the number of source points.

        Notes
        -----
        The items are, in order:

            coefficients
                The coefficients of each source point.
            distances
                The interior distance from each support point to each
                point in the volume.
            scale_parameters
                The scale parameter of each source point.
            locations
                The location of each source point.
            exponents
                The exponent of each source point.
            influences
                The influence of each source point.
        """
        return dict(coefficients=np.array(self._source_coefficients),
                    distances=np.array(self._source_distances),
                    scale_parameters=np.array(self._source_scale_parameters),
                    locations=np.array(self._source_locations),
                    exponents=np.array(self._source_exponents),
                    influences=np.array(self.influences))

    @property
    def influences(self) -> np.ndarray[float]:
        """ Influence of each source point through the volume. """
        influence = np.exp(-(np.array(self._source_distances) /
                           (np.array(self._source_exponents) *
                            np.array(self._source_scale_parameters)).reshape(-1, 1, 1, 1)) **
                           np.array(self._source_exponents).reshape(-1, 1, 1, 1))
        # Normalize so that largest value is 1 for all source points.
        influence = influence / influence.reshape(len(influence), -1).max(-1).reshape(-1, 1, 1, 1)
        # Normalize so that all influences sum to 1.
        influence[:, self._volume_mask] = (
                influence[:, self._volume_mask] / influence[:, self._volume_mask].sum(0)[None, ...])
        influence[:, ~self._volume_mask] = 0.
        return influence

    def __str__(self) -> str:
        wdt = 74
        s = []
        s += ['-' * wdt]
        s += [self.__class__.__name__.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=4, edgeitems=2, precision=5, linewidth=60):
            s += ['{:18} : {}'.format('shape', self.shape)]
            s += ['{:18} : {}'.format('distance_radius', self.distance_radius)]
            s += ['{:18} : {}'.format('basis_set (hash)', hex(hash(self.basis_set))[2:8])]
            s += ['{:18} : {}'.format('sources', len(self._source_distances))]

        s += ['-' * wdt]
        return '\n'.join(s)

    def _repr_html_(self) -> str:
        s = []
        s += [f'<h3>{self.__class__.__name__}</h3>']
        s += ['<table border="1" class="dataframe">']
        s += ['<thead><tr><th style="text-align: left;">Field</th><th>Size</th><th>Data</th></tr></thead>']
        s += ['<tbody>']
        with np.printoptions(threshold=4, edgeitems=2, precision=2, linewidth=40):
            s += ['<tr><td style="text-align: left;">shape</td>']
            s += [f'<td>1</td><td>{self.shape}</td></tr>']
            s += ['<tr><td style="text-align: left;">distance_radius</td>']
            s += [f'<td>1</td><td>{self.distance_radius}</td></tr>']
            s += ['<tr><td style="text-align: left;">basis_set (hash)</td>']
            s += [f'<td>{len(hex(hash(self.basis_set)))}</td><td>{hex(hash(self.basis_set))[2:8]}</td></tr>']
            s += ['<tr><td style="text-align: left;">sources</td>']
            s += [f'<td>1</td><td>{len(self._source_distances)}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)
