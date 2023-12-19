//===----------------------------------------------------------------------===//
//
// Copyright (C) 2022 Sophgo Technologies Inc.  All rights reserved.
//
// TPU-MLIR is licensed under the 2-Clause BSD License except for the
// third-party components.
//
//===----------------------------------------------------------------------===//

#include "tpu_mlir/Conversion/TopToTpu/LoweringBM1684.h"

namespace tpu_mlir {
namespace bm1684 {

void ModLowering::LoweringF32(PatternRewriter &rewriter, top::ModOp op) const {
  lowering_common_f32<tpu::ModOp>(rewriter, op);
}

void ModLowering::LoweringINT8(PatternRewriter &rewriter, top::ModOp op,
                               bool asymmetric) const {
  lowering_common_f32<tpu::ModOp>(rewriter, op);
}

} // namespace bm1684x
} // namespace tpu_mlir

