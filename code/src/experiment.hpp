#ifndef _EXPERIMENT_HPP_
#define _EXPERIMENT_HPP_
#include "data_io.hpp"
#include "plug-in_est.hpp"
#include <functional>
#include <string>


template <typename IN_T, typename OUT_T, template <typename> typename DIST_T>
void discrete_exp(std::string exp_name, DIST_T<IN_T> dist, std::function<OUT_T(std::map<IN_T, size_t> &, size_t)> func, const IN_T input_range_from, const IN_T input_range_to, const size_t numSamples, const size_t numIterations, const size_t numTargets, const size_t numAttackers, const size_t maxNumSpecs) {
    const std::uint64_t seed = 12345;

    plug_in_est<IN_T, OUT_T, DIST_T> estimator(seed, dist);
    std::map<size_t, std::map<IN_T, entType>> awae_data;

    for (size_t numSpecs = 1; numSpecs < maxNumSpecs; numSpecs++) {
        std::map<IN_T, entType> awae_vals;
        for (IN_T j = input_range_from; j <= input_range_to; j++) {
            // need to insert loop where computation is repeated by numIterations
            awae_vals.insert({j, estimator.estimate_leakage(func, numSamples, numTargets, numAttackers, numSpecs, {j}, input_range_from, input_range_to)});
        }
        awae_data.insert({numSpecs, awae_vals});
    }
    discrete_data<IN_T, OUT_T, DIST_T> dd = {exp_name,
                                             dist,
                                             numSamples,
                                             numTargets,
                                             numAttackers,
                                             numIterations,
                                             estimator.target_init_entropy,
                                             awae_data};

    writeJSON_discrete<IN_T, OUT_T, DIST_T>(dd);
}
void batch_exp(std::string);



#endif // _EXPERIMENT_HPP_