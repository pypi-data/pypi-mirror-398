# from vnerrant.cli.convert import m2_to_m2, parallel_to_m2


# def test_parallel_to_m2():
#     orig_file = "vnerrant/data/demo_origs.txt"
#     corr_file = "vnerrant/data/demo_hyps.txt"
#     output_path = "vnerrant/data/demo_output.m2"
#     tok, lev, merge = "spacy", False, "rules"

#     args = [
#         "--orig_file",
#         orig_file,
#         "--corr_files",
#         corr_file,
#         "--output",
#         output_path,
#         "--tok",
#         tok,
#         "--lev",
#         lev,
#         "--merge",
#         merge,
#     ]

#     parallel_to_m2(args, standalone_mode=False)


# def test_m2_to_m2():
#     m2_file = "vnerrant/data/demo_output.m2"
#     output_path = "vnerrant/data/changed_demo_output.m2"
#     merge = "rules"
#     auto, gold, no_min, old_cats, lev = False, False, False, False, False

#     args = [
#         "--input",
#         m2_file,
#         "--output",
#         output_path,
#         "--merge",
#         merge,
#     ]
#     if auto:
#         args.append("--auto")
#     if gold:
#         args.append("--gold")
#     if no_min:
#         args.append("--no_min")
#     if old_cats:
#         args.append("--old_cats")
#     if lev:
#         args.append("--lev")

#     m2_to_m2(args, standalone_mode=False)
