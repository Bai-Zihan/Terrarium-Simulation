import unittest

from terrarium.cli import build_parser


class CliParserTests(unittest.TestCase):
    def test_seed_can_appear_before_subcommand(self) -> None:
        args = build_parser().parse_args(["--seed", "42", "run", "--ticks", "2"])

        self.assertEqual(args.seed, 42)
        self.assertEqual(args.command, "run")

    def test_seed_can_appear_after_subcommand(self) -> None:
        args = build_parser().parse_args(["run", "--ticks", "2", "--seed", "42"])

        self.assertEqual(args.seed, 42)
        self.assertEqual(args.command, "run")


if __name__ == "__main__":
    unittest.main()
