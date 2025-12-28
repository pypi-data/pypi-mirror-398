
# soyml

<img src="./media/soymilk2.png" width="96">

**soy**ml: framework-independent ML model inference

_soy_ - a prefix indicating that this is a subpar substitute for the real thing :)

## pitch

machine learning models are often trained in one framework (e.g. pytorch) and deployed in another. there are many different inference-focused frameworks, but they all have different APIs. this makes it difficult to deploy models in a framework-agnostic way. soyml aims to solve this problem by providing a simple, framework-agnostic API for inference, abstracting away the details of the underlying framework, and just letting you turn **inputs** to **outputs** and nothing else.

## features

currently supported backends:
+ [pytorch](https://pytorch.org/) (`torch`)
+ [onnxruntime](https://github.com/microsoft/onnxruntime) (`ort`)
+ [wonnx](https://github.com/webonnx/wonnx) (`wonnx`)
+ [ncnn](https://github.com/Tencent/ncnn) (`ncnn`)
