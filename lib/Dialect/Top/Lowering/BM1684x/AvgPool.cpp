//===----------------------------------------------------------------------===//
//
// Copyright (c) 2020-2030 by Sophgo Technologies Inc. All rights reserved.
//
// Licensed under the Apache License v2.0.
// See http://www.apache.org/licenses/LICENSE-2.0 for license information.
// SPDX-License-Identifier: Apache-2.0
//
//===----------------------------------------------------------------------===//

#include "../Lowering.h"
#include "tpu_mlir/Dialect/Top/IR/TopOps.h"
#include "tpu_mlir/Dialect/Tpu/IR/TpuOps.h"
#include "tpu_mlir/Support/Helper/Quant.h"
#include "tpu_mlir/Support/MathUtils.h"

using namespace mlir;
using namespace tpu_mlir;
using namespace tpu_mlir::helper;

Value top::AvgPoolOp::lowering_int8_bm1684x(bool asymmetric) {
  const size_t kernel_size = kernel_shape().size();
  auto kernel = Module::getI64Array(kernel_shape());
  int64_t kd = kernel_size == 3 ? kernel->at(0) : 1;
  int64_t kh = kernel_size == 3 ? kernel->at(1) : kernel->at(0);
  int64_t kw =
      kernel_size == 3 ? kernel->at(2) : (kernel_size == 2 ? kernel->at(1) : 1);

  auto op = getOperation();
  auto ctx = getContext();
  OpBuilder builder(ctx);
  std::vector<NamedAttribute> attrs;
  for (auto &attr : op->getAttrs()) {
    attrs.push_back(attr);
  }
  double in_scale, out_scale;
  int64_t in_zp, out_zp;
  Quant::getScaleAndZeroPoint(input(), in_scale, in_zp, asymmetric);
  Quant::getScaleAndZeroPoint(output(), out_scale, out_zp, asymmetric);
  if (asymmetric == false && kernel_size != 3) {
    assert(in_zp == 0 && out_zp == 0);
    double scale = in_scale / (out_scale * kh * kw);
    int multiplier, rshift;
    get_scale_and_shift(scale, multiplier, rshift, 8);
    attrs.push_back(builder.getNamedAttr(
        "multiplier", builder.getI64IntegerAttr(multiplier)));
    attrs.push_back(
        builder.getNamedAttr("rshift", builder.getI64IntegerAttr(rshift)));
  } else {
    double scale_factor = in_scale / (kd * kh * kw * out_scale);
    double offset_factor = out_zp - in_scale / out_scale * in_zp;
    attrs.push_back(
        builder.getNamedAttr("scale", builder.getF64FloatAttr(scale_factor)));
    attrs.push_back(
        builder.getNamedAttr("offset", builder.getF64FloatAttr(offset_factor)));
  }

  builder.setInsertionPointAfter(op);
  auto newType = Quant::getQuantInt8Type(output(), asymmetric);
  if (kernel_size == 1) {
    auto newOp =
        builder.create<tpu::AvgPool1DOp>(getLoc(), newType, ValueRange{input()},
                                         ArrayRef<NamedAttribute>{attrs});
    return newOp.output();
  } else if (kernel_size == 2) {
    auto newOp =
        builder.create<tpu::AvgPool2DOp>(getLoc(), newType, ValueRange{input()},
                                         ArrayRef<NamedAttribute>{attrs});
    return newOp.output();
  } else {
    auto newOp =
        builder.create<tpu::AvgPool3DOp>(getLoc(), newType, ValueRange{input()},
                                         ArrayRef<NamedAttribute>{attrs});
    return newOp.output();
  }
}

Value top::AvgPoolOp::lowering_f32_bm1684x() {
  Value newValue;
  if (kernel_shape().size() == 3) {
    newValue = lowering_common_float<tpu::AvgPool3DOp>(getOperation());
  } else if (kernel_shape().size() == 2) {
    newValue = lowering_common_float<tpu::AvgPool2DOp>(getOperation());
  } else {
    newValue = lowering_common_float<tpu::AvgPool1DOp>(getOperation());
  }
  return newValue;
}

Value top::AvgPoolOp::lowering_bf16_bm1684x() {
  Value newValue;
  if (kernel_shape().size() == 3) {
    newValue =
        lowering_common_float<tpu::AvgPool3DOp, BFloat16Type>(getOperation());
  } else if (kernel_shape().size() == 2) {
    newValue =
        lowering_common_float<tpu::AvgPool2DOp, BFloat16Type>(getOperation());
  } else {
    newValue =
        lowering_common_float<tpu::AvgPool1DOp, BFloat16Type>(getOperation());
  }
  return newValue;
}

Value top::AvgPoolOp::lowering_f16_bm1684x() {
  Value newValue;
  if (kernel_shape().size() == 3) {
    newValue =
        lowering_common_float<tpu::AvgPool3DOp, Float16Type>(getOperation());
  } else if (kernel_shape().size() == 2) {
    newValue =
        lowering_common_float<tpu::AvgPool2DOp, Float16Type>(getOperation());
  } else {
    newValue =
        lowering_common_float<tpu::AvgPool1DOp, Float16Type>(getOperation());
  }
  return newValue;
}

Value top::AvgPoolOp::lowering_quant_bm1684x() {
  if (false == Quant::isUniformQuantized(input(), output())) {
    llvm_unreachable("input output should be quantized");
  }
  bool is_pool3d = kernel_shape().size() == 3;
  // input to f32
  Builder builder(getContext());
  auto in_f32 = do_cast(input(), builder.getF32Type(), false);
  auto op = getOperation();
  op->setOperand(0, in_f32);
  auto type = output().getType();
  Value newValue;
  if (kernel_shape().size() == 3) {
    newValue = lowering_common_float<tpu::AvgPool3DOp>(getOperation());
  } else if (kernel_shape().size() == 2) {
    newValue = lowering_common_float<tpu::AvgPool2DOp>(getOperation());
  } else {
    newValue = lowering_common_float<tpu::AvgPool1DOp>(getOperation());
  }
  return do_cast(newValue, type, true);
}
