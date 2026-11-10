"""Additional coding problems so the bank covers easy, medium, and hard practice."""


def _starter(python: str) -> dict:
    return {
        "python": python,
        "java": (
            "import java.util.Scanner;\n"
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        Scanner scanner = new Scanner(System.in);\n"
            "        // Write the Java solution here. Python is fully supported.\n"
            "    }\n"
            "}\n"
        ),
        "cpp": (
            "#include <iostream>\n"
            "int main() {\n"
            "    // Write the C++ solution here. Python is fully supported.\n"
            "    return 0;\n"
            "}\n"
        ),
    }


EXTRA_PROBLEMS = [
    {
        "slug_title": "Reverse a string",
        "topic": "Strings",
        "difficulty": "easy",
        "statement": "Read one line and print it reversed. Do not add spaces.",
        "company": "tcs",
        "starter": _starter("line = input()\n"),
        "tests": [("hello\n", "olleh\n", False), ("Placement\n", "tnemecalP\n", True)],
    },
    {
        "slug_title": "Palindrome check",
        "topic": "Strings",
        "difficulty": "easy",
        "statement": "Read one word and print yes if it is a palindrome, otherwise no. Ignore case.",
        "company": "infosys",
        "starter": _starter("word = input().strip().lower()\n"),
        "tests": [("madam\n", "yes\n", False), ("Hello\n", "no\n", True)],
    },
    {
        "slug_title": "Factorial",
        "topic": "Math",
        "difficulty": "easy",
        "statement": "Read an integer n (0 <= n <= 12) and print n factorial.",
        "company": "tcs",
        "starter": _starter("n = int(input())\n"),
        "tests": [("5\n", "120\n", False), ("0\n", "1\n", True)],
    },
    {
        "slug_title": "Maximum of a list",
        "topic": "Arrays",
        "difficulty": "easy",
        "statement": "Read one line of space-separated integers and print the maximum.",
        "company": "tcs",
        "starter": _starter("numbers = list(map(int, input().split()))\n"),
        "tests": [("4 1 9 2\n", "9\n", False), ("3 3 3\n", "3\n", True)],
    },
    {
        "slug_title": "Count words",
        "topic": "Strings",
        "difficulty": "easy",
        "statement": "Read one line and print how many words it contains. Words are separated by spaces.",
        "company": "infosys",
        "starter": _starter("line = input().strip()\n"),
        "tests": [("hello world from campus\n", "4\n", False), ("single\n", "1\n", True)],
    },
    {
        "slug_title": "Sum of digits",
        "topic": "Math",
        "difficulty": "easy",
        "statement": "Read a non-negative integer and print the sum of its digits.",
        "company": "infosys",
        "starter": _starter("value = input().strip()\n"),
        "tests": [("409\n", "13\n", False), ("1000\n", "1\n", True)],
    },
    {
        "slug_title": "Longest word length",
        "topic": "Strings",
        "difficulty": "easy",
        "statement": "Read one line of words and print the length of the longest word.",
        "company": "tcs",
        "starter": _starter("words = input().split()\n"),
        "tests": [("placement season starts\n", "9\n", False), ("a bb\n", "2\n", True)],
    },
    {
        "slug_title": "Fibonacci number",
        "topic": "DSA",
        "difficulty": "medium",
        "statement": "Read n (1 <= n <= 20) and print the nth Fibonacci number. The sequence starts 1, 1, 2, 3, 5.",
        "company": "amazon",
        "starter": _starter("n = int(input())\n"),
        "tests": [("6\n", "8\n", False), ("1\n", "1\n", True)],
    },
    {
        "slug_title": "Valid parentheses",
        "topic": "DSA",
        "difficulty": "medium",
        "statement": "Read one string of brackets ()[]{} and print yes if it is balanced, otherwise no.",
        "company": "amazon",
        "starter": _starter("text = input().strip()\n"),
        "tests": [("()[]{}\n", "yes\n", False), ("([)]\n", "no\n", True)],
    },
    {
        "slug_title": "Anagram check",
        "topic": "Strings",
        "difficulty": "medium",
        "statement": "Read two lines. Print yes if they are anagrams, ignoring spaces and case, otherwise no.",
        "company": "infosys",
        "starter": _starter("first = input()\nsecond = input()\n"),
        "tests": [("listen\nsilent\n", "yes\n", False), ("hello\nworld\n", "no\n", True)],
    },
    {
        "slug_title": "Unique words in order",
        "topic": "Strings",
        "difficulty": "medium",
        "statement": "Read one line of words and print the unique words in first-seen order, separated by spaces.",
        "company": "tcs",
        "starter": _starter("words = input().split()\n"),
        "tests": [("a b a c b\n", "a b c\n", False), ("one one\n", "one\n", True)],
    },
    {
        "slug_title": "Second largest",
        "topic": "Arrays",
        "difficulty": "medium",
        "statement": "Read space-separated integers. Print the second largest distinct value, or none if it does not exist.",
        "company": "tcs",
        "starter": _starter("numbers = list(map(int, input().split()))\n"),
        "tests": [("5 1 5 3\n", "3\n", False), ("2 2\n", "none\n", True)],
    },
    {
        "slug_title": "Prime check",
        "topic": "Math",
        "difficulty": "medium",
        "statement": "Read an integer n (n >= 2) and print yes if it is prime, otherwise no.",
        "company": "infosys",
        "starter": _starter("n = int(input())\n"),
        "tests": [("7\n", "yes\n", False), ("9\n", "no\n", True)],
    },
    {
        "slug_title": "Two sum exists",
        "topic": "DSA",
        "difficulty": "medium",
        "statement": "The first line is a target integer. The second line is space-separated integers. Print yes if two different values add up to the target, otherwise no.",
        "company": "amazon",
        "starter": _starter("target = int(input())\nnumbers = list(map(int, input().split()))\n"),
        "tests": [("9\n2 7 11 15\n", "yes\n", False), ("10\n1 2 3\n", "no\n", True)],
    },
    {
        "slug_title": "Merge two sorted lines",
        "topic": "DSA",
        "difficulty": "hard",
        "statement": "Read two lines of space-separated sorted integers. Print one merged sorted line, separated by spaces.",
        "company": "amazon",
        "starter": _starter("left = list(map(int, input().split()))\nright = list(map(int, input().split()))\n"),
        "tests": [("1 4 6\n2 3 8\n", "1 2 3 4 6 8\n", False), ("1\n2 2\n", "1 2 2\n", True)],
    },
    {
        "slug_title": "First non-repeating character",
        "topic": "Strings",
        "difficulty": "hard",
        "statement": "Read one word and print the first character that appears once. If every character repeats, print none.",
        "company": "infosys",
        "starter": _starter("word = input().strip()\n"),
        "tests": [("swiss\n", "w\n", False), ("aabb\n", "none\n", True)],
    },
]
