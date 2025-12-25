#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <pybind11/iostream.h>
#include <vector>
#include <cmath>
#include <string>
#include <iostream>
#include <omp.h>
namespace py = pybind11;

struct RectMatchResult {
	std::vector<float> phi;
	std::vector<float> eta;
	std::vector<int> sampling;
	std::vector<unsigned long> id;
	std::vector<float> et;
	std::vector<std::vector<unsigned int>> shape;
};

struct Seed {
	float phi;
	float eta;
};

float phi_mpi_pi(float phi) {
	while (phi >= M_PI) phi -= 2*M_PI;
	while (phi < -M_PI) phi += 2*M_PI;
	return phi;
}

RectMatchResult cluster(
		py::array_t<float> cells_phi,
		py::array_t<float> cells_eta,
		py::array_t<int> cells_sampling,
		py::array_t<unsigned long> cells_id,
		py::array_t<float> seeds_phi,
		py::array_t<float> seeds_eta,
		py::array_t<unsigned int> shape_seeds,
		py::array_t<unsigned long> gepcells_id,
		py::array_t<float> gepcells_et,
		py::array_t<unsigned int> shape_gepcells,
		float phi_delta,
		float eta_delta
		) {
	auto cells_phi_buf  = cells_phi.unchecked<1>();
	auto cells_eta_buf = cells_eta.unchecked<1>();
	auto cells_sampling_buf = cells_sampling.unchecked<1>();
	auto cells_id_buf = cells_id.unchecked<1>();

	auto seeds_phi_buf = seeds_phi.unchecked<1>();
	auto seeds_eta_buf = seeds_eta.unchecked<1>();
	auto shape_seeds_buf = shape_seeds.unchecked<1>();

	auto gepcells_id_buf = gepcells_id.unchecked<1>();
	auto gepcells_et_buf = gepcells_et.unchecked<1>();
	auto shape_gepcells_buf = shape_gepcells.unchecked<1>();

	RectMatchResult res;
	ssize_t n_cells = cells_phi_buf.shape(0);

	// Preallocate per-thread buffers
	int nthreads = omp_get_max_threads();
	std::vector<RectMatchResult> thread_results(nthreads);

	ssize_t flat_seed_index = 0;

	ssize_t n_events = shape_seeds_buf.shape(0);

	ssize_t flat_gepcells_index = 0;
	std::vector<std::unordered_map<unsigned long, float>> gep_maps;
	std::vector<std::vector<Seed>> seed_lists;
	for (ssize_t ev = 0; ev < n_events; ++ev) {
		// Build a fast lookup map for each event
		std::unordered_map<unsigned long, float> gep_map;
		gep_map.reserve(shape_gepcells_buf(ev));
		for (unsigned int i = 0; i < shape_gepcells_buf(ev); ++i) {
			gep_map[gepcells_id_buf(flat_gepcells_index + i)] =
				gepcells_et_buf(flat_gepcells_index + i);
		}
		gep_maps.push_back(gep_map);
		flat_gepcells_index += shape_gepcells_buf(ev);

		std::vector<Seed> seeds;
		for (unsigned int i = 0; i < shape_seeds_buf(ev); ++i) {
			Seed seed;
			seed.phi = seeds_phi_buf(flat_seed_index + i);
			seed.eta = seeds_eta_buf(flat_seed_index + i);
			seeds.push_back(seed);
		}
		seed_lists.push_back(seeds);
		flat_seed_index += shape_seeds_buf(ev);
	}

#pragma omp parallel
	{
		int tid = omp_get_thread_num();
		auto& local_res = thread_results[tid];

#pragma omp for ordered schedule(static)
		for (ssize_t ev = 0; ev < n_events; ++ev) {
			std::vector<unsigned int> n_cells_in_cluster_vec;
			for (auto seed : seed_lists[ev]) {
				unsigned int n_cells_in_cluster = 0;
				for (ssize_t k = 0; k < n_cells; ++k) {
					float dphi = cells_phi_buf(k) - seed.phi;
					dphi = phi_mpi_pi(dphi);
					dphi = std::abs(dphi);

					float deta = std::abs(cells_eta_buf(k) - seed.eta);

					if (dphi < phi_delta && deta < eta_delta) {
						n_cells_in_cluster ++;
						unsigned long cell_id = cells_id_buf(k);
						local_res.phi.push_back(cells_phi_buf(k));
						local_res.eta.push_back(cells_eta_buf(k));
						local_res.id.push_back(cell_id);
						local_res.sampling.push_back(cells_sampling_buf(k));

						auto it = gep_maps[ev].find(cell_id);
						local_res.et.push_back(it != gep_maps[ev].end() ? it->second : 0.0f);
					}
				}
				n_cells_in_cluster_vec.push_back(n_cells_in_cluster);
			}
			local_res.shape.push_back(n_cells_in_cluster_vec);
		}
	}

	// Merge thread-local results into the final result
	size_t total_size = 0;
	for (auto& t : thread_results) total_size += t.phi.size();

	res.phi.reserve(total_size);
	res.eta.reserve(total_size);
	res.id.reserve(total_size);
	res.sampling.reserve(total_size);
	res.et.reserve(total_size);
	res.shape.reserve(n_events);

	for (auto& t : thread_results) {
		res.phi.insert(res.phi.end(), t.phi.begin(), t.phi.end());
		res.eta.insert(res.eta.end(), t.eta.begin(), t.eta.end());
		res.id.insert(res.id.end(), t.id.begin(), t.id.end());
		res.sampling.insert(res.sampling.end(), t.sampling.begin(), t.sampling.end());
		res.et.insert(res.et.end(), t.et.begin(), t.et.end());
		res.shape.insert(res.shape.end(), t.shape.begin(), t.shape.end());
	}

	return res;
}

PYBIND11_MODULE(clustering_cpp_openmp_impl, m) {
	py::class_<RectMatchResult>(m, "RectMatchResult")
		.def_readonly("phi", &RectMatchResult::phi)
		.def_readonly("eta", &RectMatchResult::eta)
		.def_readonly("et", &RectMatchResult::et)
		.def_readonly("sampling", &RectMatchResult::sampling)
		.def_readonly("id", &RectMatchResult::id)
		.def_readonly("shape", &RectMatchResult::shape);


	m.def("cluster", &cluster,
			"Cluster cells around seeds with GEP matching",
			py::arg("cells_phi"), py::arg("cells_eta"), py::arg("cells_sampling"), py::arg("cells_id"),
			py::arg("seeds_phi"), py::arg("seeds_eta"), py::arg("shape_gepcells"),
			py::arg("gepcells_id"), py::arg("gepcells_et"),
			py::arg("shape_gepcells"),
			py::arg("phi_delta"), py::arg("eta_delta"),
			py::call_guard<py::scoped_ostream_redirect,
			py::scoped_estream_redirect>()); 

}

