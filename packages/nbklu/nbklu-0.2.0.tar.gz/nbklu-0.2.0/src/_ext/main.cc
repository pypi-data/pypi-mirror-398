#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>
#include <klu.h>
#include "docstrings.h"

namespace nb = nanobind;

NB_MODULE(_ext, m) {
  m.doc() = "Raw KLU sparse solver Python bindings";

  // Define klu_common struct wrapper
  nb::class_<klu_common>(m, "Common", doc_klu_common.c_str())
      .def(nb::init<>())
      .def("defaults", &klu_defaults, doc_klu_common_defaults.c_str())
      .def_rw("tol", &klu_common::tol, doc_klu_common_tol.c_str())
      .def_rw("memgrow", &klu_common::memgrow, doc_klu_common_memgrow.c_str())
      .def_rw("initmem_amd", &klu_common::initmem_amd,
              doc_klu_common_initmem_amd.c_str())
      .def_rw("initmem", &klu_common::initmem, doc_klu_common_initmem.c_str())
      .def_rw("maxwork", &klu_common::maxwork, doc_klu_common_maxwork.c_str())
      .def_rw("btf", &klu_common::btf, doc_klu_common_btf.c_str())
      .def_rw("ordering", &klu_common::ordering,
              doc_klu_common_ordering.c_str())
      .def_rw("scale", &klu_common::scale, doc_klu_common_scale.c_str())
      // user_order
      // user_data
      .def_rw("halt_if_singular", &klu_common::halt_if_singular,
              doc_klu_common_halt_if_singular.c_str())
      .def_rw("status", &klu_common::status, doc_klu_common_status.c_str())
      .def_rw("nrealloc", &klu_common::nrealloc,
              doc_klu_common_nrealloc.c_str())
      .def_rw("structural_rank", &klu_common::structural_rank,
              doc_klu_common_structural_rank.c_str())
      .def_rw("numerical_rank", &klu_common::numerical_rank,
              doc_klu_common_numerical_rank.c_str())
      .def_rw("singular_col", &klu_common::singular_col,
              doc_klu_common_singular_col.c_str())
      .def_rw("noffdiag", &klu_common::noffdiag,
              doc_klu_common_noffdiag.c_str())
      .def_rw("flops", &klu_common::flops, doc_klu_common_flops.c_str())
      .def_rw("rcond", &klu_common::rcond, doc_klu_common_rcond.c_str())
      .def_rw("condest", &klu_common::condest, doc_klu_common_condest.c_str())
      .def_rw("rgrowth", &klu_common::rgrowth, doc_klu_common_rgrowth.c_str())
      .def_rw("work", &klu_common::work, doc_klu_common_work.c_str())
      .def_rw("memusage", &klu_common::memusage,
              doc_klu_common_memusage.c_str())
      .def_rw("mempeak", &klu_common::mempeak, doc_klu_common_mempeak.c_str());

  // Define klu_symbolic struct wrapper
  nb::class_<klu_symbolic>(m, "Symbolic", doc_klu_symbolic.c_str())
      .def("free", [](klu_symbolic *self,
                      klu_common *common) { klu_free_symbolic(&self, common); })
      .def_rw("symmetry", &klu_symbolic::symmetry,
              doc_klu_symbolic_symmetry.c_str())
      .def_rw("est_flops", &klu_symbolic::est_flops,
              doc_klu_symbolic_est_flops.c_str())
      .def_rw("lnz", &klu_symbolic::lnz, doc_klu_symbolic_lnz.c_str())
      .def_rw("unz", &klu_symbolic::unz, doc_klu_symbolic_unz.c_str())
      .def_rw("n", &klu_symbolic::n, doc_klu_symbolic_n.c_str())
      .def_rw("nz", &klu_symbolic::nz, doc_klu_symbolic_nz.c_str())
      .def_rw("nzoff", &klu_symbolic::nzoff, doc_klu_symbolic_nzoff.c_str())
      .def_rw("nblocks", &klu_symbolic::nblocks,
              doc_klu_symbolic_nblocks.c_str())
      .def_rw("maxblock", &klu_symbolic::maxblock,
              doc_klu_symbolic_maxblock.c_str())
      .def_rw("ordering", &klu_symbolic::ordering,
              doc_klu_symbolic_ordering.c_str())
      .def_rw("do_btf", &klu_symbolic::do_btf, doc_klu_symbolic_do_btf.c_str())
      .def_rw("structural_rank", &klu_symbolic::structural_rank,
              doc_klu_symbolic_structural_rank.c_str());

  // Define klu_numeric struct wrapper
  nb::class_<klu_numeric>(m, "Numeric")
      .def("free", [](klu_numeric *self,
                      klu_common *common) { klu_free_numeric(&self, common); })
      .def_rw("n", &klu_numeric::n, doc_klu_numeric_n.c_str())
      .def_rw("nblocks", &klu_numeric::nblocks, doc_klu_numeric_nblocks.c_str())
      .def_rw("lnz", &klu_numeric::lnz, doc_klu_numeric_lnz.c_str())
      .def_rw("unz", &klu_numeric::unz, doc_klu_numeric_unz.c_str())
      .def_rw("max_lnz_block", &klu_numeric::max_lnz_block,
              doc_klu_numeric_max_lnz_block.c_str())
      .def_rw("max_unz_block", &klu_numeric::max_unz_block,
              doc_klu_numeric_max_unz_block.c_str())
      .def_rw("nzoff", &klu_numeric::nzoff, doc_klu_numeric_nzoff.c_str());

  // KLU status constants
  m.attr("KLU_OK") = KLU_OK;
  m.attr("KLU_SINGULAR") = KLU_SINGULAR;
  m.attr("KLU_OUT_OF_MEMORY") = KLU_OUT_OF_MEMORY;
  m.attr("KLU_INVALID") = KLU_INVALID;
  m.attr("KLU_TOO_LARGE") = KLU_TOO_LARGE;

  // KLU functions
  m.def(
      "analyze",
      [](int32_t n, const nb::ndarray<int32_t> &Ap,
         const nb::ndarray<int32_t> &Ai, klu_common *common) {
        return klu_analyze(n, Ap.data(), Ai.data(), common);
      },
      nb::arg("n"), nb::arg("Ap"), nb::arg("Ai"), nb::arg("common"),
      doc_klu_analyze.c_str());

  m.def(
      "analyze_given",
      [](int32_t n, const nb::ndarray<int32_t> &Ap,
         const nb::ndarray<int32_t> &Ai, const nb::ndarray<int32_t> &Puser,
         const nb::ndarray<int32_t> &Quser, klu_common *common) {
        return klu_analyze_given(n, Ap.data(), Ai.data(), Puser.data(),
                                 Quser.data(), common);
      },
      nb::arg("n"), nb::arg("Ap"), nb::arg("Ai"), nb::arg("Puser").none(),
      nb::arg("Quser").none(), nb::arg("common"),
      doc_klu_analyze_given.c_str());

  m.def(
      "factor",
      [](const nb::ndarray<int32_t> &Ap, const nb::ndarray<int32_t> &Ai,
         const nb::ndarray<double> &Ax, klu_symbolic *symbolic,
         klu_common *common) {
        return klu_factor(Ap.data(), Ai.data(), Ax.data(), symbolic, common);
      },
      nb::arg("Ap"), nb::arg("Ai"), nb::arg("Ax"), nb::arg("symbolic"),
      nb::arg("common"), doc_klu_factor.c_str());

  m.def(
      "solve",
      [](klu_symbolic *symbolic, klu_numeric *numeric, int32_t ldim,
         int32_t nrhs, nb::ndarray<double> &B, klu_common *common) {
        return klu_solve(symbolic, numeric, ldim, nrhs, B.data(), common);
      },
      nb::arg("symbolic"), nb::arg("numeric"), nb::arg("ldim"), nb::arg("nrhs"),
      nb::arg("B"), nb::arg("common"), doc_klu_solve.c_str());

  m.def(
      "tsolve",
      [](klu_symbolic *symbolic, klu_numeric *numeric, int32_t ldim,
         int32_t nrhs, nb::ndarray<double> &B, klu_common *common) {
        return klu_tsolve(symbolic, numeric, ldim, nrhs, B.data(), common);
      },
      nb::arg("symbolic"), nb::arg("numeric"), nb::arg("ldim"), nb::arg("nrhs"),
      nb::arg("B"), nb::arg("common"), doc_klu_tsolve.c_str());

  m.def(
      "refactor",
      [](const nb::ndarray<int32_t> &Ap, const nb::ndarray<int32_t> &Ai,
         const nb::ndarray<double> &Ax, klu_symbolic *symbolic,
         klu_numeric *numeric, klu_common *common) {
        return klu_refactor(
            const_cast<int32_t *>(Ap.data()), const_cast<int32_t *>(Ai.data()),
            const_cast<double *>(Ax.data()), symbolic, numeric, common);
      },
      nb::arg("Ap"), nb::arg("Ai"), nb::arg("Ax"), nb::arg("symbolic"),
      nb::arg("numeric"), nb::arg("common"), doc_klu_refactor.c_str());

  m.def(
      "sort",
      [](klu_symbolic *symbolic, klu_numeric *numeric, klu_common *common) {
        return klu_sort(symbolic, numeric, common);
      },
      nb::arg("symbolic"), nb::arg("numeric"), nb::arg("common"),
      doc_klu_sort.c_str());

  m.def(
      "flops",
      [](klu_symbolic *symbolic, klu_numeric *numeric, klu_common *common) {
        return klu_flops(symbolic, numeric, common);
      },
      nb::arg("symbolic"), nb::arg("numeric"), nb::arg("common"),
      doc_klu_flops.c_str());

  m.def(
      "rgrowth",
      [](nb::ndarray<int32_t> Ap, nb::ndarray<int32_t> Ai,
         nb::ndarray<double> Ax, klu_symbolic *symbolic, klu_numeric *numeric,
         klu_common *common) {
        return klu_rgrowth(Ap.data(), Ai.data(), Ax.data(), symbolic, numeric,
                           common);
      },
      nb::arg("Ap"), nb::arg("Ai"), nb::arg("Ax"), nb::arg("symbolic"),
      nb::arg("numeric"), nb::arg("common"), doc_klu_rgrowth.c_str());

  m.def(
      "condest",
      [](nb::ndarray<int32_t> Ap, nb::ndarray<double> Ax,
         klu_symbolic *symbolic, klu_numeric *numeric, klu_common *common) {
        return klu_condest(Ap.data(), Ax.data(), symbolic, numeric, common);
      },
      nb::arg("Ap"), nb::arg("Ax"), nb::arg("symbolic"), nb::arg("numeric"),
      nb::arg("common"), doc_klu_condest.c_str());

  m.def(
      "rcond",
      [](klu_symbolic *symbolic, klu_numeric *numeric, klu_common *common) {
        return klu_rcond(symbolic, numeric, common);
      },
      nb::arg("symbolic"), nb::arg("numeric"), nb::arg("common"),
      doc_klu_rcond.c_str());

  m.def(
      "scale",
      [](int32_t scale, int32_t n, nb::ndarray<int32_t> Ap,
         nb::ndarray<int32_t> Ai, nb::ndarray<double> Ax,
         nb::ndarray<double> Rs, nb::ndarray<int32_t> W, klu_symbolic *symbolic,
         klu_numeric *numeric, klu_common *common) {
        return klu_scale(scale, n, Ap.data(), Ai.data(), Ax.data(), Rs.data(),
                         W.data(), common);
      },
      nb::arg("scale"), nb::arg("n"), nb::arg("Ap"), nb::arg("Ai"),
      nb::arg("Ax"), nb::arg("Rs"), nb::arg("W"), nb::arg("symbolic"),
      nb::arg("numeric"), nb::arg("common"), doc_klu_scale.c_str());

  m.def(
      "extract",
      [](klu_numeric *numeric, klu_symbolic *symbolic, nb::ndarray<int32_t> Lp,
         nb::ndarray<int32_t> Li, nb::ndarray<double> Lx,
         nb::ndarray<int32_t> Up, nb::ndarray<int32_t> Ui,
         nb::ndarray<double> Ux, nb::ndarray<int32_t> Fp,
         nb::ndarray<int32_t> Fi, nb::ndarray<double> Fx,
         nb::ndarray<int32_t> P, nb::ndarray<int32_t> Q, nb::ndarray<double> Rs,
         nb::ndarray<int32_t> R, klu_common *Common) {
        klu_extract(numeric, symbolic, Lp.data(), Li.data(), Lx.data(),
                    Up.data(), Ui.data(), Ux.data(), Fp.data(), Fi.data(),
                    Fx.data(), P.data(), Q.data(), Rs.data(), R.data(), Common);
      },
      nb::arg("numeric"), nb::arg("symbolic"), nb::arg("Lp"), nb::arg("Li"),
      nb::arg("Lx"), nb::arg("Up"), nb::arg("Ui"), nb::arg("Ux"), nb::arg("Fp"),
      nb::arg("Fi"), nb::arg("Fx"), nb::arg("P"), nb::arg("Q"), nb::arg("Rs"),
      nb::arg("R"), nb::arg("common"), doc_klu_extract.c_str());
}
