/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* AttrDef Declarations                                                       *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

#ifdef GET_ATTRDEF_CLASSES
#undef GET_ATTRDEF_CLASSES


namespace mlir {
class AsmParser;
class AsmPrinter;
} // namespace mlir
namespace mlir::triton::gluon {

/// An encoding that is inferred from neighboring ops in the graph.
class AutoEncodingAttr;
class AutoEncodingAttr : public ::mlir::Attribute::AttrBase<AutoEncodingAttr, ::mlir::Attribute, ::mlir::AttributeStorage> {
public:
  using Base::Base;
  static constexpr ::llvm::StringLiteral name = "gluon.auto_encoding";
  static constexpr ::llvm::StringLiteral dialectName = "gluon";
  static constexpr ::llvm::StringLiteral getMnemonic() {
    return {"auto_encoding"};
  }

};

} // namespace mlir::triton::gluon
MLIR_DECLARE_EXPLICIT_TYPE_ID(::mlir::triton::gluon::AutoEncodingAttr)

#endif // GET_ATTRDEF_CLASSES

