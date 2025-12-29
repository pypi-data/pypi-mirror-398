/* Copyright 2025 Daniil Shmelev
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================================= */

#include "cupch.h"
#include "cusig.h"
 //#include "cuda_constants.h"
#include "cu_sig_coeff.h"



// https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#atomic-functions
__device__ double myAtomicAdd(double* address, double val)
{
	unsigned long long int* address_as_ull =
		(unsigned long long int*)address;
	unsigned long long int old = *address_as_ull, assumed;

	do {
		assumed = old;
		old = atomicCAS(address_as_ull, assumed,
			__double_as_longlong(val +
				__longlong_as_double(assumed)));

		// Note: uses integer comparison to avoid hang in case of NaN (since NaN != NaN)
	} while (assumed != old);

	return __longlong_as_double(old);
}


template<typename T>
__device__ void single_sig_coeff_(
	const double* path,
	double* out,
	const uint64_t* multi_idx,
	uint64_t degree,
	uint64_t dimension,
	uint64_t length,
	double* prev_coeffs,
	double* next_coeffs,
	double* incr_prod,
	const double* one_over_fact,
	const int num_threads
) {
	const int blockId = blockIdx.x;
	const int thread_id = threadIdx.x;

	double* next_pt = path + dimension;
	double* prev_pt = path;
	double* const path_end = path + dimension * length;

	if (thread_id == 0) {
		prev_coeffs[0] = 1.;
		next_coeffs[0] = 1.;
		incr_prod[0] = 1.;

		for (uint64_t i = 1; i < degree + 1; ++i) {
			incr_prod[i] = incr_prod[i - 1] * static_cast<double>(next_pt[multi_idx[i - 1]] - prev_pt[multi_idx[i - 1]]);
		}
	}

	for (uint64_t i = thread_id + 1; i < degree + 1; i += num_threads) {
		prev_coeffs[i] = incr_prod[i] * one_over_fact[i];
	}

	for (; next_pt != path_end; next_pt += dimension, prev_pt += dimension) {

		// incr_prod here takes a different role than before
		// At step i, incr_prod[i - k] = prod_{j=k}^i incr[j]

		for (uint64_t i = 1; i < degree + 1; ++i) {

			__syncthreads();

			if (thread_id == 0) {
				next_coeffs[i] = prev_coeffs[i];

				const double new_incr = static_cast<double>(next_pt[multi_idx[i - 1]] - prev_pt[multi_idx[i - 1]]);
				incr_prod[i] = new_incr;
			}

			for (uint64_t k = thread_id + 1; k < i; k += num_threads) {
				incr_prod[k] *= new_incr;
			}

			for (uint64_t k = thread_id + 1; k <= i; k += num_threads) {
				double update = prev_coeffs[i - k] * incr_prod[i - k + 1] * one_over_fact[k];
				myAtomicAdd(next_coeffs[i], update);
			}
		}

		__syncthreads();

		std::swap(next_coeffs, prev_coeffs);
	}

	__syncthreads();

	if (thread_id == 0)
		*out = prev_coeffs[degree];
}


template<typename T>
__global__ void get_sig_coeff_(
	const T* path,
	double* out,
	const uint64_t* multi_idx,
	uint64_t num_multi_idx, // len(multi_idx)
	const uint64_t* degrees, // [ len(multi_index[i]) for i in 0:num_multi_index ]
	uint64_t dimension,
	uint64_t length,
	bool time_aug,
	bool lead_lag,
	double end_time
) {

	if (dimension == 0) { throw std::invalid_argument("sig_coeff received path of dimension 0"); }

	if (length <= 1) {
		std::fill(out, out + num_multi_idx, 0.);
		return;
	}

	//TODO: check indices < dim

	Path<T> path_obj(path, dimension, length, time_aug, lead_lag, end_time);

	double* out_ptr = out;

	// Each buffer is of length (len(multi_indices[i]) + 1)
	// So we need a total size of sum{ len(multi_indices[i]) + 1 } = sum{ len(multi_indices[i]) } + len(multi_indices)
	uint64_t coeff_buffer_len = num_multi_idx;
	uint64_t max_degree = 0;

	for (uint64_t i = 0; i < num_multi_idx; ++i) {
		coeff_buffer_len += degrees[i];
		max_degree = std::max(max_degree, degrees[i]);
	}

	auto incr_prod_uptr = std::make_unique<double[]>(max_degree + 1);
	double* incr_prod = incr_prod_uptr.get();

	auto one_over_fact_uptr = std::make_unique<double[]>(max_degree + 1);
	double* one_over_fact = one_over_fact_uptr.get();

	one_over_fact[0] = 1.;
	for (uint64_t i = 1; i < max_degree + 1; ++i) {
		one_over_fact[i] = one_over_fact[i - 1] / i;
	}

	auto prev_coeffs_uptr = std::make_unique<double[]>(coeff_buffer_len);
	double* prev_coeffs = prev_coeffs_uptr.get();

	auto next_coeffs_uptr = std::make_unique<double[]>(coeff_buffer_len);
	double* next_coeffs = next_coeffs_uptr.get();

	const uint64_t* multi_idx_ptr = multi_idx;

	for (uint64_t i = 0; i < num_multi_idx; ++i) {
		single_sig_coeff_<T>(path_obj, out_ptr, multi_idx_ptr, degrees[i], prev_coeffs, next_coeffs, incr_prod, one_over_fact);
		++out_ptr;
		prev_coeffs += degrees[i] + 1;
		next_coeffs += degrees[i] + 1;
		multi_idx_ptr += degrees[i];
	}

}

template<typename T>
void batch_sig_coeff_(
	const T* path,
	double* out,
	const uint64_t* multi_idx,
	uint64_t num_multi_idx, // len(multi_idx)
	const uint64_t* degrees, // [ len(multi_index[i]) for i in 0:num_multi_index ]
	uint64_t batch_size,
	uint64_t dimension,
	uint64_t length,
	bool time_aug,
	bool lead_lag,
	double end_time,
	int n_jobs
)
{
	//Deal with trivial cases
	if (dimension == 0) { throw std::invalid_argument("sig_coeff received path of dimension 0"); }

	Path<T> dummy_path_obj(nullptr, dimension, length, time_aug, lead_lag, end_time); //Work with path_obj to capture time_aug, lead_lag transformations

	//General case and degree = 1 case
	const uint64_t flat_path_length = dimension * length;
	const T* const data_end = path + flat_path_length * batch_size;

	std::function<void(const T*, double*)> sig_func;

	sig_func = [&](const T* path_ptr, double* out_ptr) {
		sig_coeff_<T>(path_ptr, out_ptr, multi_idx, num_multi_idx, degrees, dimension, length, time_aug, lead_lag, end_time);
		};

	const T* path_ptr;
	double* out_ptr;

	if (n_jobs != 1) {
		multi_threaded_batch(sig_func, path, out, batch_size, flat_path_length, num_multi_idx, n_jobs);
	}
	else {
		for (path_ptr = path, out_ptr = out;
			path_ptr < data_end;
			path_ptr += flat_path_length, out_ptr += num_multi_idx) {

			sig_func(path_ptr, out_ptr);
		}
	}
	return;
}


#define SAFE_CALL(function_call)                            \
    try {                                                   \
        function_call;                                      \
    }                                                       \
    catch (std::bad_alloc&) {					            \
		std::cerr << "Failed to allocate memory";           \
        return 1;                                           \
    }                                                       \
    catch (std::invalid_argument& e) {                      \
		std::cerr << e.what();					            \
        return 2;                                           \
    }                                                       \
	catch (std::out_of_range& e) {			                \
		std::cerr << e.what();					            \
		return 3;                                           \
	}  											            \
	catch (std::runtime_error& e) {							\
		std::string msg = e.what();							\
		std::regex pattern(R"(CUDA Error \((\d+)\):)");		\
		std::smatch match;									\
		int ret_code = 4;									\
		if (std::regex_search(msg, match, pattern)) {		\
			ret_code = 100000 + std::stoi(match[1]);		\
		}													\
		std::cerr << e.what();								\
		return ret_code;									\
	}														\
    catch (...) {                                           \
		std::cerr << "Unknown exception";		            \
        return 5;                                           \
    }                                                       \
    return 0;


extern "C" {

	
}
