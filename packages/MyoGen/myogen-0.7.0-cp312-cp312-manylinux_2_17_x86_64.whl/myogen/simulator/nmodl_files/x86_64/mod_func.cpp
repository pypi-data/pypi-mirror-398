#include <stdio.h>
#include "hocdec.h"
extern int nrnmpi_myid;
extern int nrn_nobanner_;
#if defined(__cplusplus)
extern "C" {
#endif

extern void _caL_reg(void);
extern void _constant_reg(void);
extern void _dummy_reg(void);
extern void _gammapointprocess_reg(void);
extern void _GammaStim_reg(void);
extern void _Gfluctdv_reg(void);
extern void _gh_reg(void);
extern void _izap_reg(void);
extern void _kdrRL_reg(void);
extern void _L_Ca_inact_reg(void);
extern void _mAHP_reg(void);
extern void _motoneuron_reg(void);
extern void _muscle_unit_calcium_reg(void);
extern void _muscle_unit_reg(void);
extern void _na3rp_reg(void);
extern void _napp_reg(void);
extern void _naps_reg(void);
extern void _nsloc_reg(void);
extern void _vecevent_reg(void);

void modl_reg() {
  if (!nrn_nobanner_) if (nrnmpi_myid < 1) {
    fprintf(stderr, "Additional mechanisms from files\n");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/caL.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/constant.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/dummy.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/gammapointprocess.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/GammaStim.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/Gfluctdv.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/gh.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/izap.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/kdrRL.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/L_Ca_inact.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/mAHP.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/motoneuron.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/muscle_unit_calcium.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/muscle_unit.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/na3rp.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/napp.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/naps.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/nsloc.mod\"");
    fprintf(stderr, " \"myogen/simulator/nmodl_files/vecevent.mod\"");
    fprintf(stderr, "\n");
  }
  _caL_reg();
  _constant_reg();
  _dummy_reg();
  _gammapointprocess_reg();
  _GammaStim_reg();
  _Gfluctdv_reg();
  _gh_reg();
  _izap_reg();
  _kdrRL_reg();
  _L_Ca_inact_reg();
  _mAHP_reg();
  _motoneuron_reg();
  _muscle_unit_calcium_reg();
  _muscle_unit_reg();
  _na3rp_reg();
  _napp_reg();
  _naps_reg();
  _nsloc_reg();
  _vecevent_reg();
}

#if defined(__cplusplus)
}
#endif
