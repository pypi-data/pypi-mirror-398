#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>
#include <nanobind/ndarray.h>
#include <klu.h>

namespace nb = nanobind;

NB_MODULE(_ext, m) {
    m.doc() = "KLU sparse solver Python bindings";

    // Define klu_common struct wrapper
    nb::class_<klu_common>(m, "Common")
        .def(nb::init<>())
        .def("defaults", &klu_defaults)
        .def_rw("tol", &klu_common::tol)
        .def_rw("memgrow", &klu_common::memgrow)
        .def_rw("initmem_amd", &klu_common::initmem_amd)
        .def_rw("initmem", &klu_common::initmem)
        .def_rw("maxwork", &klu_common::maxwork)
        .def_rw("btf", &klu_common::btf)
        .def_rw("ordering", &klu_common::ordering)
        .def_rw("scale", &klu_common::scale)
        .def_rw("halt_if_singular", &klu_common::halt_if_singular)
        .def_rw("status", &klu_common::status)
        .def_rw("nrealloc", &klu_common::nrealloc)
        .def_rw("structural_rank", &klu_common::structural_rank)
        .def_rw("numerical_rank", &klu_common::numerical_rank)
        .def_rw("singular_col", &klu_common::singular_col)
        .def_rw("noffdiag", &klu_common::noffdiag)
        .def_rw("flops", &klu_common::flops)
        .def_rw("rcond", &klu_common::rcond)
        .def_rw("condest", &klu_common::condest)
        .def_rw("rgrowth", &klu_common::rgrowth)
        .def_rw("work", &klu_common::work)
        .def_rw("memusage", &klu_common::memusage)
        .def_rw("mempeak", &klu_common::mempeak);

    // Define klu_symbolic struct wrapper
    nb::class_<klu_symbolic>(m, "Symbolic")
        .def("free", [](klu_symbolic* self, klu_common* common) {
            klu_free_symbolic(&self, common);
        })
        .def_rw("symmetry", &klu_symbolic::symmetry)
        .def_rw("est_flops", &klu_symbolic::est_flops)
        .def_rw("lnz", &klu_symbolic::lnz)
        .def_rw("unz", &klu_symbolic::unz)
        .def_rw("n", &klu_symbolic::n)
        .def_rw("nz", &klu_symbolic::nz)
        .def_rw("nzoff", &klu_symbolic::nzoff)
        .def_rw("nblocks", &klu_symbolic::nblocks)
        .def_rw("maxblock", &klu_symbolic::maxblock)
        .def_rw("ordering", &klu_symbolic::ordering)
        .def_rw("do_btf", &klu_symbolic::do_btf)
        .def_rw("structural_rank", &klu_symbolic::structural_rank);

    // Define klu_numeric struct wrapper
    nb::class_<klu_numeric>(m, "Numeric")
        .def("free", [](klu_numeric* self, klu_common* common) {
            klu_free_numeric(&self, common);
        })
        .def_rw("n", &klu_numeric::n)
        .def_rw("nblocks", &klu_numeric::nblocks)
        .def_rw("lnz", &klu_numeric::lnz)
        .def_rw("unz", &klu_numeric::unz)
        .def_rw("max_lnz_block", &klu_numeric::max_lnz_block)
        .def_rw("max_unz_block", &klu_numeric::max_unz_block)
        .def_rw("nzoff", &klu_numeric::nzoff);

    // KLU status constants
    m.attr("KLU_OK") = KLU_OK;
    m.attr("KLU_SINGULAR") = KLU_SINGULAR;
    m.attr("KLU_OUT_OF_MEMORY") = KLU_OUT_OF_MEMORY;
    m.attr("KLU_INVALID") = KLU_INVALID;
    m.attr("KLU_TOO_LARGE") = KLU_TOO_LARGE;

    // KLU functions
    m.def("analyze", [](int32_t n, const nb::ndarray<int32_t>& Ap, const nb::ndarray<int32_t>& Ai, klu_common* common) {
        return klu_analyze(n, Ap.data(), Ai.data(), common);
    });

    m.def("analyze_given", [](int32_t n, const nb::ndarray<int32_t>& Ap, const nb::ndarray<int32_t>& Ai, const nb::ndarray<int32_t>& P, const nb::ndarray<int32_t>& Q, klu_common* common) {
        return klu_analyze_given(n, Ap.data(), Ai.data(), P.data(), Q.data(), common);
    });

    m.def("factor", [](const nb::ndarray<int32_t>& Ap, const nb::ndarray<int32_t>& Ai, const nb::ndarray<double>& Ax, klu_symbolic* symbolic, klu_common* common) {
        return klu_factor(Ap.data(), Ai.data(), Ax.data(), symbolic, common);
    });

    m.def("solve",
          [](klu_symbolic *symbolic, klu_numeric *numeric, int32_t ldim,
             int32_t nrhs, nb::ndarray<double> &B, klu_common *common) {
            return klu_solve(symbolic, numeric, ldim, nrhs, B.data(), common);
          });

    // m.def("tsolve", [](klu_symbolic* symbolic, klu_numeric* numeric, int32_t ldim, int32_t nrhs, double* B, klu_common* common) {
    //     return klu_tsolve(symbolic, numeric, ldim, nrhs, B, common);
    // });

    // m.def("refactor", [](const int32_t* Ap, const int32_t* Ai, const double* Ax, klu_symbolic* symbolic, klu_numeric* numeric, klu_common* common) {
    //     return klu_refactor(const_cast<int32_t*>(Ap), const_cast<int32_t*>(Ai), const_cast<double*>(Ax), symbolic, numeric, common);
    // });
}
