"""
----------------------------------------------------------------------
>>> Author       : Junshan Yin  
>>> Last Updated : 2025-11-22
----------------------------------------------------------------------
"""

from junshan_kit import ModelsHub

def check_args(args, parser, allowed_models, allowed_optimizers, allowed_datasets):
    # Parse and validate each train_group
    for cfg in args.train:
        model, dataset, optimizer = cfg.split("-")

        if model not in allowed_models:
            parser.error(f"Invalid model '{model}'. Choose from {allowed_models}")

        if optimizer not in allowed_optimizers:
            parser.error(f"Invalid optimizer '{optimizer}'. Choose from {allowed_optimizers}")

        if dataset not in allowed_datasets:
            print(type(allowed_datasets), allowed_datasets)
            parser.error(f"Invalid dataset '{dataset}'. Choose from {allowed_datasets}")


    # Check if the model-dataset-optimizer combination exists
    for cfg in args.train:
        model_name, dataset_name, optimizer_name = cfg.split("-")
        try:
            f = getattr(ModelsHub, f"Build_{args.model_name_mapping[model_name]}_{args.data_name_mapping[dataset_name]}")

        except:
            print(getattr(ModelsHub, f"Build_{args.model_name_mapping[model_name]}_{args.data_name_mapping[dataset_name]}"))
            assert False
        
    # Check epochs or iterations
    if args.e is None and args.iter is None:
        parser.error("one of --e or --iter must be specified")
    
    if args.e is not None and args.iter is not None:
        parser.error("one of --e or --iter must be specified")

def check_subset_info(args, parser):
        total = sum(args.subset)
        if args.subset[0]>1:
            # CHECK
            for i in args.subset:
                if i < 1:
                    parser.error(f"Invalid --subset {args.subset}: The number of subdata must > 1")    
        else:
            if abs(total - 1.0) != 0.0:  
                parser.error(f"Invalid --subset {args.subset}: the values must sum to 1.0 (current sum = {total:.6f}))")
