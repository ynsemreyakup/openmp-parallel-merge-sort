#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <omp.h>
#include <random>
#include <vector>

using Clock = std::chrono::steady_clock;

struct RunResult {
    double seconds;
    std::uint64_t checksum;
    bool is_sorted;
};

std::vector<int> create_random_input(std::size_t element_count) {
    std::vector<int> values(element_count);
    std::mt19937 generator(42);
    std::uniform_int_distribution<int> distribution(0, 1'000'000'000);

    for (std::size_t i = 0; i < values.size(); ++i) {
        values[i] = distribution(generator);
    }
    return values;
}

std::uint64_t calculate_checksum(const std::vector<int>& values) {
    std::uint64_t sum = 0;
    for (int value : values) {
        sum += static_cast<std::uint64_t>(value);
    }
    return sum;
}

void merge_sorted_ranges(
    std::vector<int>& values,
    std::vector<int>& buffer,
    int left,
    int middle,
    int right
) {
    int left_index = left;
    int right_index = middle;
    int output_index = left;

    while (left_index < middle && right_index < right) {
        if (values[left_index] <= values[right_index]) {
            buffer[output_index++] = values[left_index++];
        } else {
            buffer[output_index++] = values[right_index++];
        }
    }

    while (left_index < middle) {
        buffer[output_index++] = values[left_index++];
    }
    while (right_index < right) {
        buffer[output_index++] = values[right_index++];
    }

    for (int i = left; i < right; ++i) {
        values[i] = buffer[i];
    }
}

void sequential_merge_sort(
    std::vector<int>& values,
    std::vector<int>& buffer,
    int left,
    int right
) {
    if (right - left <= 1) {
        return;
    }

    int middle = left + (right - left) / 2;
    sequential_merge_sort(values, buffer, left, middle);
    sequential_merge_sort(values, buffer, middle, right);
    merge_sorted_ranges(values, buffer, left, middle, right);
}

void parallel_merge_sort(
    std::vector<int>& values,
    std::vector<int>& buffer,
    int left,
    int right,
    int remaining_task_depth
) {
    if (right - left <= 1) {
        return;
    }

    int middle = left + (right - left) / 2;

    if (remaining_task_depth > 0) {
#pragma omp task shared(values, buffer)
        parallel_merge_sort(values, buffer, left, middle, remaining_task_depth - 1);

#pragma omp task shared(values, buffer)
        parallel_merge_sort(values, buffer, middle, right, remaining_task_depth - 1);

#pragma omp taskwait
    } else {
        sequential_merge_sort(values, buffer, left, middle);
        sequential_merge_sort(values, buffer, middle, right);
    }

    merge_sorted_ranges(values, buffer, left, middle, right);
}

RunResult run_sequential_version(const std::vector<int>& input) {
    std::vector<int> values = input;
    std::vector<int> buffer(values.size());

    auto start = Clock::now();
    sequential_merge_sort(values, buffer, 0, static_cast<int>(values.size()));
    auto end = Clock::now();

    return {
        std::chrono::duration<double>(end - start).count(),
        calculate_checksum(values),
        std::is_sorted(values.begin(), values.end())
    };
}

int choose_task_depth(int thread_count) {
    int depth = 0;
    for (int threads = thread_count; threads > 1; threads >>= 1) {
        ++depth;
    }
    return depth + 2;
}

RunResult run_parallel_version(const std::vector<int>& input, int thread_count) {
    std::vector<int> values = input;
    std::vector<int> buffer(values.size());
    omp_set_num_threads(thread_count);

    int task_depth = choose_task_depth(thread_count);

    auto start = Clock::now();
#pragma omp parallel
    {
#pragma omp single
        parallel_merge_sort(values, buffer, 0, static_cast<int>(values.size()), task_depth);
    }
    auto end = Clock::now();

    return {
        std::chrono::duration<double>(end - start).count(),
        calculate_checksum(values),
        std::is_sorted(values.begin(), values.end())
    };
}

double median(std::vector<double> values) {
    std::sort(values.begin(), values.end());
    return values[values.size() / 2];
}

int main(int argc, char** argv) {
    std::size_t element_count = argc > 1
        ? static_cast<std::size_t>(std::strtoull(argv[1], nullptr, 10))
        : 5'000'000;
    int repeat_count = argc > 2 ? std::atoi(argv[2]) : 5;

    std::vector<int> input = create_random_input(element_count);
    std::cout << "mode,threads,n,median_seconds,checksum,sorted,speedup,efficiency\n";

    std::vector<double> sequential_times;
    RunResult sequential_result{};
    for (int repeat = 0; repeat < repeat_count; ++repeat) {
        sequential_result = run_sequential_version(input);
        sequential_times.push_back(sequential_result.seconds);
    }

    double sequential_median = median(sequential_times);
    std::cout << "sequential,1," << element_count << ","
              << std::fixed << std::setprecision(6) << sequential_median << ","
              << sequential_result.checksum << ","
              << (sequential_result.is_sorted ? "true" : "false")
              << ",1.0000,1.0000\n";

    int max_threads = omp_get_max_threads();
    std::vector<int> thread_counts = {2, 4, 8, 12, 16};

    for (int thread_count : thread_counts) {
        if (thread_count > max_threads) {
            continue;
        }

        std::vector<double> parallel_times;
        RunResult parallel_result{};
        for (int repeat = 0; repeat < repeat_count; ++repeat) {
            parallel_result = run_parallel_version(input, thread_count);
            parallel_times.push_back(parallel_result.seconds);
        }

        double parallel_median = median(parallel_times);
        double speedup = sequential_median / parallel_median;
        double efficiency = speedup / thread_count;

        std::cout << "openmp," << thread_count << "," << element_count << ","
                  << std::fixed << std::setprecision(6) << parallel_median << ","
                  << parallel_result.checksum << ","
                  << (parallel_result.is_sorted ? "true" : "false") << ","
                  << std::setprecision(4) << speedup << ","
                  << std::setprecision(4) << efficiency << "\n";
    }

    return 0;
}
