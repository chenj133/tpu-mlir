//===----------------------------------------------------------------------===//
//
// Copyright (C) 2022 Sophgo Technologies Inc.  All rights reserved.
//
// TPU-MLIR is licensed under the 2-Clause BSD License except for the
// third-party components.
//
//===----------------------------------------------------------------------===//

#include "tpu_mlir/Dialect/Top/IR/TopOps.h"
#include "tpu_mlir/Support/Helper/Module.h"
#include "tpu_mlir/Support/MathUtils.h"

using namespace tpu_mlir;
using namespace tpu_mlir::helper;
using namespace mlir;


int64_t top::HardSigmoidOp::getFLOPs() {
  return Module::getNumElements(output()) * 4;
}

LogicalResult top::HardSigmoidOp::init(InferenceParameter &p) { return success(); }
void top::HardSigmoidOp::deinit(InferenceParameter &p) {}

static inline double hsigmoid(double x, double alpha, double beta) {
  return std::max(0.0, std::min(1.0, alpha * x + beta)) ;
}

LogicalResult top::HardSigmoidOp::inference(InferenceParameter &p) {
  const auto num_element = Module::getNumElements(output());
  const double alpha_ = alpha().convertToDouble();
  const double beta_ = beta().convertToDouble();
#pragma omp parallel for schedule(static, omp_schedule(num_element))
  for (int i = 0; i < num_element; ++i) {
    p.outputs[0][i] = hsigmoid(p.inputs[0][i], alpha_, beta_);
  }
  return success();
}
