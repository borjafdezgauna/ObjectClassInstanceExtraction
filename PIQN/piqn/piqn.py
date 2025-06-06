import argparse

from args import train_argparser, eval_argparser
from config_reader import process_configs
from piqn import input_reader
from piqn.piqn_trainer import PIQNTrainer
import warnings

warnings.filterwarnings("ignore")

def __train(run_args):
    trainer = PIQNTrainer(run_args)
    trainer.train(train_path=run_args.train_path, valid_path=run_args.valid_path,
                  types_path=run_args.types_path, input_reader_cls=input_reader.JsonInputReader)


def _train():
    arg_parser = train_argparser()
    process_configs(target=__train, arg_parser=arg_parser)


def __eval(run_args):
    trainer = PIQNTrainer(run_args)
    trainer.eval(dataset_path=run_args.dataset_path, types_path=run_args.types_path,
                 input_reader_cls=input_reader.JsonInputReader)


def _eval():
    arg_parser = eval_argparser()
    process_configs(target=__eval, arg_parser=arg_parser)


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser(add_help=False)
    arg_parser.add_argument('mode', type=str, help="Mode: 'train', 'eval' or 'init'")
    args, _ = arg_parser.parse_known_args()

    if args.mode == 'download':
        from utils.preprocess_data import download
        download("10.5281/zenodo.14982480","93rRIrmMoXStzcSXDFRLuOl9s4dShff63FfEherDK2M4DBrcQUzH2v6fBSKJ")
    elif args.mode == 'preprocess':
        from utils.preprocess_data import preprocess_files
        preprocess_files()
    elif args.mode == 'train':
        _train()
    elif args.mode == 'eval':
        _eval()
    else:
        raise Exception("Mode not in ['train', 'eval', 'init'], e.g. 'python piqn.py train ...'")
