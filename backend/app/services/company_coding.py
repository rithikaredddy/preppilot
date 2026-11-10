"""Coding tasks for companies that otherwise have only interview prompts."""


def _starters(python: str) -> dict:
    return {
        "python": python,
        "java": (
            "import java.util.Scanner;\n"
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        Scanner scanner = new Scanner(System.in);\n"
            "        // Read the input and print the answer.\n"
            "        if (scanner.hasNextLine()) {\n"
            "            System.out.println(scanner.nextLine());\n"
            "        }\n"
            "    }\n"
            "}\n"
        ),
        "cpp": (
            "#include <iostream>\n"
            "#include <string>\n"
            "int main() {\n"
            "    std::string line;\n"
            "    std::getline(std::cin, line);\n"
            "    // Print the answer.\n"
            "    std::cout << line << std::endl;\n"
            "    return 0;\n"
            "}\n"
        ),
    }


def _problem(title, company, topic, difficulty, statement, python, tests):
    return {
        "slug_title": title,
        "topic": topic,
        "difficulty": difficulty,
        "statement": statement,
        "company": company,
        "starter": _starters(python),
        "tests": tests,
    }


COMPANY_CODING_PROBLEMS = [
    _problem(
        "Even or odd",
        "accenture",
        "Math",
        "easy",
        "Read one integer and print even or odd.",
        "n = int(input())\n",
        [("4\n", "even\n", False), ("7\n", "odd\n", True)],
    ),
    _problem(
        "Double the number",
        "accenture",
        "Math",
        "easy",
        "Read one integer and print twice its value.",
        "n = int(input())\n",
        [("6\n", "12\n", False), ("0\n", "0\n", True)],
    ),
    _problem(
        "Letter count",
        "accenture",
        "Strings",
        "easy",
        "Read one word and print how many letters it contains.",
        "word = input().strip()\n",
        [("hello\n", "5\n", False), ("a\n", "1\n", True)],
    ),
    _problem(
        "Last digit",
        "capgemini",
        "Math",
        "easy",
        "Read a non-negative integer and print its last digit.",
        "n = input().strip()\n",
        [("409\n", "9\n", False), ("10\n", "0\n", True)],
    ),
    _problem(
        "Add one",
        "capgemini",
        "Math",
        "easy",
        "Read one integer and print the next integer.",
        "n = int(input())\n",
        [("7\n", "8\n", False), ("-1\n", "0\n", True)],
    ),
    _problem(
        "Repeat the word",
        "capgemini",
        "Strings",
        "easy",
        "Read one word and print it twice, separated by a space.",
        "word = input().strip()\n",
        [("hi\n", "hi hi\n", False), ("ok\n", "ok ok\n", True)],
    ),
    _problem(
        "Smaller of two",
        "cognizant",
        "Math",
        "easy",
        "Read two integers on one line and print the smaller one.",
        "a, b = map(int, input().split())\n",
        [("3 8\n", "3\n", False), ("9 2\n", "2\n", True)],
    ),
    _problem(
        "Absolute value",
        "cognizant",
        "Math",
        "easy",
        "Read one integer and print its absolute value.",
        "n = int(input())\n",
        [("-4\n", "4\n", False), ("4\n", "4\n", True)],
    ),
    _problem(
        "Sum from one to n",
        "cognizant",
        "Math",
        "medium",
        "Read n (1 <= n <= 1000) and print the sum of integers from 1 through n.",
        "n = int(input())\n",
        [("4\n", "10\n", False), ("1\n", "1\n", True)],
    ),
    _problem(
        "Has a vowel",
        "google",
        "Strings",
        "easy",
        "Read one word and print yes if it contains a vowel, otherwise no. Matching is case-insensitive.",
        "word = input().strip().lower()\n",
        [("cat\n", "yes\n", False), ("rhythm\n", "no\n", True)],
    ),
    _problem(
        "Largest of three",
        "google",
        "Arrays",
        "easy",
        "Read three integers on one line and print the largest.",
        "numbers = list(map(int, input().split()))\n",
        [("1 9 3\n", "9\n", False), ("4 4 2\n", "4\n", True)],
    ),
    _problem(
        "Pair sums to target",
        "google",
        "DSA",
        "medium",
        "The first line is a target. The second line is space-separated integers. Print yes if two different values add up to the target, otherwise no.",
        "target = int(input())\nnumbers = list(map(int, input().split()))\n",
        [("5\n2 3 4\n", "yes\n", False), ("10\n1 2 3\n", "no\n", True)],
    ),
    _problem(
        "Product of two",
        "microsoft",
        "Math",
        "easy",
        "Read two integers on one line and print their product.",
        "a, b = map(int, input().split())\n",
        [("3 5\n", "15\n", False), ("0 9\n", "0\n", True)],
    ),
    _problem(
        "Remove spaces",
        "microsoft",
        "Strings",
        "easy",
        "Read one line and print it with every space removed.",
        "line = input()\n",
        [("a b c\n", "abc\n", False), ("no\n", "no\n", True)],
    ),
    _problem(
        "Balanced brackets",
        "microsoft",
        "DSA",
        "medium",
        "Read one string of round brackets and print yes if it is balanced, otherwise no.",
        "text = input().strip()\n",
        [("()()\n", "yes\n", False), ("(()\n", "no\n", True)],
    ),
    _problem(
        "Square of a number",
        "wipro",
        "Math",
        "easy",
        "Read one integer and print its square.",
        "n = int(input())\n",
        [("6\n", "36\n", False), ("0\n", "0\n", True)],
    ),
    _problem(
        "Count the digits",
        "wipro",
        "Math",
        "easy",
        "Read a non-negative integer and print how many digits it has.",
        "value = input().strip()\n",
        [("1000\n", "4\n", False), ("7\n", "1\n", True)],
    ),
    _problem(
        "Hello name",
        "wipro",
        "Strings",
        "easy",
        "Read one name and print Hello, followed by a space and the name.",
        "name = input().strip()\n",
        [("Rithika\n", "Hello Rithika\n", False), ("Ada\n", "Hello Ada\n", True)],
    ),
]
