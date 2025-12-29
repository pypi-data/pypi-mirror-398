# from vnerrant.cli.evaluate import m2


# def test_m2_evaluation():
#     hyp = "vnerrant/data/demo_out_hyp_m2"
#     ref = "vnerrant/data/demo_out_ref_m2"
#     beta = 0.5
#     verbose = False
#     dt = False
#     ds = False
#     cse = False
#     single = False
#     multi = False
#     filter = []
#     cat = 1

#     args = [
#         "-hyp",
#         hyp,
#         "-ref",
#         ref,
#         "-b",
#         beta,
#         "-filt",
#         filter,
#         "-cat",
#         cat,
#     ]
#     if verbose:
#         args.append("-v")
#     if dt:
#         args.append("-dt")
#     if ds:
#         args.append("-ds")
#     if cse:
#         args.append("-cse")
#     if single:
#         args.append("-single")
#     if multi:
#         args.append("-multi")

#     m2(args, standalone_mode=False)
