"""Campus question banks. These are commonly reported placement prompts, not private transcripts."""


def _q(category: str, topic: str, difficulty: str, prompt: str, tip: str) -> dict:
    return {
        "category": category,
        "topic": topic,
        "difficulty": difficulty,
        "prompt": prompt,
        "preparation_tip": tip,
    }


EXTRA_BY_SLUG = {
    "amazon": [
        _q("hr", "Leadership", "intermediate", "Tell me about a time you took ownership of a problem nobody else was handling.", "Name the problem, what you did without being asked, and the result."),
        _q("technical", "System design", "advanced", "How would you design a URL shortener for a campus event?", "Start with the API, then the key store, then what happens when two people request the same code."),
        _q("coding", "DSA", "intermediate", "Find the first non-repeating character in a string.", "Say the two-pass count approach and its time and space cost."),
        _q("technical", "DBMS", "intermediate", "When would you choose a composite index?", "Give one query whose WHERE clause matches the column order."),
    ],
    "tcs": [
        _q("hr", "Introduction", "beginner", "Introduce yourself in under a minute, including one project.", "Use name, branch, one project, and the role you want. Stop there."),
        _q("technical", "OOP", "beginner", "What is the difference between method overloading and overriding?", "Give one example of each in a single sentence."),
        _q("coding", "Python", "beginner", "Read a line of numbers and print the maximum.", "Mention what you do when the line has one number."),
        _q("technical", "SQL", "beginner", "Write a query to find the second highest salary.", "Say whether you use a subquery, LIMIT, or a window function."),
    ],
    "infosys": [
        _q("hr", "Communication", "beginner", "Describe a time you explained a technical idea to a non-technical teammate.", "Drop the jargon and name what the teammate understood at the end."),
        _q("technical", "DBMS", "beginner", "What is a primary key, and can it be null?", "State the uniqueness rule and the null rule separately."),
        _q("coding", "Strings", "beginner", "Check whether a word is a palindrome.", "Mention case and spaces before you write the loop."),
        _q("technical", "OS", "intermediate", "What is the difference between a process and a thread?", "Use memory sharing as the distinction, then one example."),
    ],
}

MORE_COMPANIES = [
    {
        "slug": "wipro",
        "name": "Wipro",
        "overview": "Wipro campus rounds usually mix a short HR chat, aptitude-style basics, and one programming question.",
        "questions": [
            _q("hr", "Introduction", "beginner", "Why do you want to join Wipro, and what role are you aiming for?", "Connect one skill you already have to the role. Skip generic praise."),
            _q("technical", "Python", "beginner", "What is the difference between a list and a tuple?", "Mention mutability and one case where a tuple is the better choice."),
            _q("coding", "Arrays", "beginner", "Count how many words are in a sentence.", "Define what you treat as a word when there are extra spaces."),
            _q("technical", "CN", "beginner", "What happens when you type a URL and press enter?", "Walk DNS, TCP, then HTTP in that order."),
            _q("hr", "Projects", "beginner", "Which part of your project did you build alone?", "Name the module, the language, and one bug you fixed."),
        ],
    },
    {
        "slug": "accenture",
        "name": "Accenture",
        "overview": "Accenture placement screens often check communication, a project walkthrough, and programming fundamentals.",
        "questions": [
            _q("hr", "Communication", "beginner", "Tell me about a deadline you almost missed.", "State the deadline, the action you took, and what shipped."),
            _q("technical", "OOP", "intermediate", "Explain encapsulation with a field from your project.", "Show a private field and the method that changes it."),
            _q("coding", "Math", "beginner", "Print the factorial of n for n up to 12.", "Say what you return for 0."),
            _q("technical", "SQL", "intermediate", "What is the difference between an inner join and a left join?", "Use students and courses as the two tables."),
            _q("hr", "Goals", "beginner", "Where do you see yourself after the training period?", "Name a skill you want to be trusted with, not a job title only."),
        ],
    },
    {
        "slug": "cognizant",
        "name": "Cognizant",
        "overview": "Cognizant GenC-style rounds commonly include HR, a technical basics round, and a simple coding task.",
        "questions": [
            _q("hr", "Introduction", "beginner", "Walk me through your education and one achievement outside class.", "Keep the achievement to two sentences with a result."),
            _q("technical", "DBMS", "beginner", "What is normalization, and why stop at third normal form?", "Give one anomaly that 3NF removes."),
            _q("coding", "Strings", "beginner", "Reverse a string without using a library reverse.", "Mention whether you build a new string or swap in place."),
            _q("technical", "OS", "beginner", "What is deadlock, and name one way to avoid it?", "State the four conditions briefly, then one prevention idea."),
            _q("coding", "Math", "beginner", "Check whether a number is prime.", "Mention that 1 is not prime."),
        ],
    },
    {
        "slug": "microsoft",
        "name": "Microsoft",
        "overview": "Microsoft campus interviews usually go deeper on problem solving, one coding round, and a project discussion.",
        "questions": [
            _q("coding", "DSA", "intermediate", "Given a sorted array, return the index of a target or say it is missing.", "State binary search and the empty-array case."),
            _q("coding", "DSA", "advanced", "Merge two sorted lists into one sorted list.", "Compare the heads and say the time cost."),
            _q("technical", "OOP", "intermediate", "When would you use composition instead of inheritance?", "Give one example where inheritance would force a wrong 'is-a' relationship."),
            _q("hr", "Projects", "intermediate", "Tell me about a bug that took you more than a day to find.", "Describe the symptom, how you isolated it, and the fix."),
            _q("technical", "System design", "advanced", "How would you design a rate limiter for a login API?", "Name the key, the window, and what the client sees when limited."),
        ],
    },
    {
        "slug": "google",
        "name": "Google",
        "overview": "Google-style campus rounds focus on data structures, clear communication, and how you test your own solution.",
        "questions": [
            _q("coding", "DSA", "intermediate", "Two numbers in an array add up to a target. Say if such a pair exists.", "Start with the nested loop, then the hash-set version."),
            _q("coding", "DSA", "advanced", "Check whether a string of brackets is balanced.", "Name the stack and one failing example."),
            _q("technical", "Algorithms", "advanced", "What is the time complexity of your solution, and can you do better?", "Give the current bound, then one idea that would change it."),
            _q("hr", "Collaboration", "intermediate", "Tell me about feedback you disagreed with and what you did next.", "Show that you understood the feedback before you say what you changed."),
            _q("technical", "Testing", "intermediate", "How do you test a function before you say it is done?", "Name the normal case, an empty input, and one boundary."),
        ],
    },
    {
        "slug": "capgemini",
        "name": "Capgemini",
        "overview": "Capgemini campus rounds often start with communication and pseudo-code, then a short technical round.",
        "questions": [
            _q("hr", "Introduction", "beginner", "Describe your final-year project to someone who does not know the domain.", "Use the user, the problem, and what your module did."),
            _q("technical", "Pseudo-code", "beginner", "Write pseudo-code to find the second largest number in a list.", "Say what you print when every value is the same."),
            _q("coding", "Arrays", "beginner", "Remove duplicate words while keeping the first occurrence.", "Mention that order should stay the same."),
            _q("technical", "CN", "beginner", "What is the difference between TCP and UDP?", "Give one campus example for each."),
            _q("hr", "Strengths", "beginner", "What is one weakness you are actively improving?", "Name the weakness and the practice you do every week."),
        ],
    },
]


def extra_questions_for(slug: str) -> list[dict]:
    return EXTRA_BY_SLUG.get(slug, [])
