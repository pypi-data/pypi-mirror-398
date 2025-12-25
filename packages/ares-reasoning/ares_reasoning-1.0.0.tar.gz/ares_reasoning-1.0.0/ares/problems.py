"""
Evaluation problems for ARES baseline testing.
Each problem has:
- id: unique identifier
- type: "math" or "logic"
- problem: the problem text
- answer: the correct answer (for verification)
- difficulty: 1-3 scale
"""

MATH_PROBLEMS = [
    {
        "id": "math_001",
        "type": "math",
        "problem": "A farmer has 3 fields. The first field has 12 apple trees. The second field has twice as many trees as the first. The third field has 5 fewer trees than the second. How many apple trees does the farmer have in total?",
        "answer": "55",
        "difficulty": 1,
        "steps": ["First: 12", "Second: 12*2=24", "Third: 24-5=19", "Total: 12+24+19=55"]
    },
    {
        "id": "math_002",
        "type": "math",
        "problem": "A store sells notebooks for $3 each and pens for $1.50 each. Emma buys 4 notebooks and 6 pens. She pays with a $20 bill. How much change does she receive?",
        "answer": "1",
        "difficulty": 1,
        "steps": ["Notebooks: 4*3=12", "Pens: 6*1.5=9", "Total: 12+9=21", "Change: 20-21=-1 (not enough!)"]
    },
    {
        "id": "math_003",
        "type": "math",
        "problem": "A train travels at 60 mph for 2 hours, then at 40 mph for 3 hours. What is the average speed for the entire journey?",
        "answer": "48",
        "difficulty": 2,
        "steps": ["Distance1: 60*2=120", "Distance2: 40*3=120", "Total distance: 240", "Total time: 5", "Avg: 240/5=48"]
    },
    {
        "id": "math_004",
        "type": "math",
        "problem": "A rectangle has a perimeter of 36 cm. If the length is 3 times the width, what is the area of the rectangle?",
        "answer": "60.75",
        "difficulty": 2,
        "steps": ["Let width=w, length=3w", "Perimeter: 2(w+3w)=36", "8w=36, w=4.5", "Length=13.5", "Area=4.5*13.5=60.75"]
    },
    {
        "id": "math_005",
        "type": "math",
        "problem": "A ball is dropped from 100 meters. Each bounce reaches 60% of the previous height. After the 3rd bounce, how high does the ball reach?",
        "answer": "21.6",
        "difficulty": 2,
        "steps": ["After 1st bounce: 100*0.6=60", "After 2nd bounce: 60*0.6=36", "After 3rd bounce: 36*0.6=21.6"]
    },
    {
        "id": "math_006",
        "type": "math",
        "problem": "In a class of 30 students, 18 play soccer, 15 play basketball, and 5 play neither. How many students play both sports?",
        "answer": "8",
        "difficulty": 2,
        "steps": ["Playing at least one: 30-5=25", "Soccer+Basketball=18+15=33", "Both: 33-25=8"]
    },
    {
        "id": "math_007",
        "type": "math",
        "problem": "A car's value depreciates by 15% each year. If it's worth $20,000 now, what will it be worth after 2 years? Round to the nearest dollar.",
        "answer": "14450",
        "difficulty": 2,
        "steps": ["After year 1: 20000*0.85=17000", "After year 2: 17000*0.85=14450"]
    },
    {
        "id": "math_008",
        "type": "math",
        "problem": "Three pipes can fill a tank. Pipe A fills it in 6 hours, Pipe B in 4 hours, Pipe C in 3 hours. How long to fill the tank with all three pipes? Give answer as a fraction.",
        "answer": "4/3",
        "difficulty": 3,
        "steps": ["Rate A: 1/6", "Rate B: 1/4", "Rate C: 1/3", "Combined: 1/6+1/4+1/3=2/12+3/12+4/12=9/12=3/4", "Time: 1/(3/4)=4/3 hours"]
    },
    {
        "id": "math_009",
        "type": "math",
        "problem": "A merchant marks up goods by 40% and then offers a 20% discount. What is the overall profit percentage?",
        "answer": "12",
        "difficulty": 2,
        "steps": ["Let cost=100", "Marked price: 100*1.4=140", "After discount: 140*0.8=112", "Profit: 12%"]
    },
    {
        "id": "math_010",
        "type": "math",
        "problem": "How many positive integers less than 100 are divisible by either 3 or 5 but not both?",
        "answer": "47",
        "difficulty": 3,
        "steps": ["Div by 3: 33", "Div by 5: 19", "Div by 15 (both): 6", "Only 3: 33-6=27", "Only 5: 19-6=13", "Total: 27+13=40"]
    }
]

LOGIC_PROBLEMS = [
    {
        "id": "logic_001",
        "type": "logic",
        "problem": """Three friends (Alice, Bob, Carol) each have a different pet (cat, dog, fish).
- Alice doesn't have the dog.
- The person with the cat is not Carol.
- Bob has the fish.

Who has which pet? Answer in format: Alice:X, Bob:Y, Carol:Z""",
        "answer": "Alice:cat, Bob:fish, Carol:dog",
        "difficulty": 1,
        "constraints": ["Alice != dog", "Carol != cat", "Bob = fish"]
    },
    {
        "id": "logic_002", 
        "type": "logic",
        "problem": """Four people (Amy, Ben, Cara, Dan) sit in a row of 4 seats (numbered 1-4 from left).
- Amy sits in an even-numbered seat.
- Ben sits immediately to the right of Cara.
- Dan sits in seat 1.

What seat is each person in? Answer in format: Amy:X, Ben:Y, Cara:Z, Dan:W""",
        "answer": "Amy:4, Ben:3, Cara:2, Dan:1",
        "difficulty": 2,
        "constraints": ["Amy in {2,4}", "Ben = Cara + 1", "Dan = 1"]
    },
    {
        "id": "logic_003",
        "type": "logic", 
        "problem": """Three boxes are labeled 'Apples', 'Oranges', and 'Mixed'. Each label is WRONG.
The 'Apples' box is opened and contains oranges.
What does each box actually contain? Answer in format: 'Apples'-box:X, 'Oranges'-box:Y, 'Mixed'-box:Z""",
        "answer": "'Apples'-box:oranges, 'Oranges'-box:mixed, 'Mixed'-box:apples",
        "difficulty": 2,
        "constraints": ["Each label is wrong", "'Apples' box has oranges", "All different"]
    },
    {
        "id": "logic_004",
        "type": "logic",
        "problem": """A says: 'B is lying.' B says: 'C is lying.' C says: 'A and B are both lying.'
If exactly one person is telling the truth, who is it?""",
        "answer": "B",
        "difficulty": 2,
        "constraints": ["Exactly one truth-teller"]
    },
    {
        "id": "logic_005",
        "type": "logic",
        "problem": """Five runners (A, B, C, D, E) finish a race. 
- A finishes before B but after C.
- D finishes last.
- E finishes immediately after A.

What is the finishing order from first to last?""",
        "answer": "C, A, E, B, D",
        "difficulty": 2,
        "constraints": ["C < A < B", "D = last", "E = A + 1"]
    }
]

ALL_PROBLEMS = MATH_PROBLEMS + LOGIC_PROBLEMS


def get_problem_by_id(problem_id: str):
    """Get a problem by its ID."""
    for p in ALL_PROBLEMS:
        if p["id"] == problem_id:
            return p
    return None


def get_problems_by_type(problem_type: str):
    """Get all problems of a given type."""
    return [p for p in ALL_PROBLEMS if p["type"] == problem_type]
