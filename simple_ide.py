import io, os, re, sys, tempfile
import streamlit as st
import subprocess
import utils

class SimpleCodeExecutor:
    def __init__(self):
        self.supported_languages = {
            'python': {
                'extension': '.py',
                'examples': {
                    'beginner': '''# Beginner: Simple Calculator
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

# Test the functions
num1 = 10
num2 = 5
print(f"{num1} + {num2} = {add(num1, num2)}")
print(f"{num1} - {num2} = {subtract(num1, num2)}")''',
                    'intermediate': '''# Intermediate: List Operations and String Manipulation
def process_student_grades(grades):
    # Calculate average
    average = sum(grades) / len(grades)
    
    # Find highest and lowest grades
    highest = max(grades)
    lowest = min(grades)
    
    # Create a formatted report
    report = f"Grade Report:\\n"
    report += f"Average: {average:.2f}\\n"
    report += f"Highest: {highest}\\n"
    report += f"Lowest: {lowest}\\n"
    
    # Count grades above average
    above_avg = len([g for g in grades if g > average])
    report += f"Grades above average: {above_avg}"
    
    return report

# Test with sample grades
grades = [85, 92, 78, 90, 88]
print(process_student_grades(grades))''',
                    'advanced': '''# Advanced: Data Analysis with Functional Programming
def analyze_text_data(texts):
    # Split texts into words and create word frequency dictionary
    words = [word.lower() for text in texts for word in text.split()]
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Find most common words (top 3)
    most_common = sorted(word_freq.items(), key=lambda x: (-x[1], x[0]))[:3]
    
    # Calculate statistics
    total_words = len(words)
    unique_words = len(word_freq)
    avg_word_length = sum(len(word) for word in words) / total_words
    
    # Find longest words (top 3)
    longest_words = sorted(set(words), key=len, reverse=True)[:3]
    
    # Create analysis report
    report = []
    report.append("=== Text Analysis Report ===")
    report.append(f"Total words: {total_words}")
    report.append(f"Unique words: {unique_words}")
    report.append(f"Average word length: {avg_word_length:.2f} characters")
    
    report.append("\\nMost common words:")
    for word, count in most_common:
        report.append(f"- '{word}': {count} times")
    
    report.append("\\nLongest words:")
    for word in longest_words:
        report.append(f"- '{word}' ({len(word)} characters)")
    
    # Word length distribution
    length_dist = {}
    for word in words:
        length = len(word)
        length_dist[length] = length_dist.get(length, 0) + 1
    
    report.append("\\nWord length distribution:")
    for length in sorted(length_dist.keys()):
        report.append(f"{length} letters: {length_dist[length]} words")
    
    return "\\n".join(report)

# Sample texts for analysis
sample_texts = [
    "The quick brown fox jumps over the lazy dog",
    "Python programming is fun and exciting",
    "Data analysis helps us understand patterns",
    "Functional programming makes code more elegant",
    "Learning new concepts is always challenging"
]

# Run the analysis
print(analyze_text_data(sample_texts))

# Additional analysis: Find words that appear in multiple texts
print("\\n=== Cross-Text Analysis ===")
text_words = [set(text.lower().split()) for text in sample_texts]
common_words = set.intersection(*text_words)
if common_words:
    print("Words appearing in all texts:")
    for word in sorted(common_words):
        print(f"- '{word}'")
else:
    print("No words appear in all texts")

# Find text similarity (number of common words between each pair)
print("\\nText similarity (common words between pairs):")
for i in range(len(sample_texts)):
    for j in range(i + 1, len(sample_texts)):
        common = len(text_words[i] & text_words[j])
        print(f"Texts {i+1} & {j+1}: {common} common words")'''
                },
                'example': '''# Example: Calculate factorial
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

number = 5
result = factorial(number)
print(f"Factorial of {number} is {result}")'''
            },
            'java': {
                'extension': '.java',
                'examples': {
                    'beginner': '''// Beginner: Simple Calculator
public class Main {
    public static void main(String[] args) {
        int num1 = 10;
        int num2 = 5;
        
        System.out.println(num1 + " + " + num2 + " = " + add(num1, num2));
        System.out.println(num1 + " - " + num2 + " = " + subtract(num1, num2));
    }
    
    public static int add(int a, int b) {
        return a + b;
    }
    
    public static int subtract(int a, int b) {
        return a - b;
    }
}''',
                    'intermediate': '''// Intermediate: Array Operations and String Formatting
public class Main {
    public static void main(String[] args) {
        int[] grades = {85, 92, 78, 90, 88};
        String report = processStudentGrades(grades);
        System.out.println(report);
    }
    
    public static String processStudentGrades(int[] grades) {
        // Calculate average
        double sum = 0;
        for (int grade : grades) {
            sum += grade;
        }
        double average = sum / grades.length;
        
        // Find highest and lowest
        int highest = grades[0];
        int lowest = grades[0];
        int aboveAvg = 0;
        
        for (int grade : grades) {
            if (grade > highest) highest = grade;
            if (grade < lowest) lowest = grade;
            if (grade > average) aboveAvg++;
        }
        
        // Create formatted report
        return String.format("Grade Report:\\n" +
                           "Average: %.2f\\n" +
                           "Highest: %d\\n" +
                           "Lowest: %d\\n" +
                           "Grades above average: %d",
                           average, highest, lowest, aboveAvg);
    }
}''',
                    'advanced': '''// Advanced: Object-Oriented Programming with Interfaces
interface Animal {
    String makeSound();
    String getInfo();
}

abstract class AbstractAnimal implements Animal {
    protected String name;
    protected String species;
    
    public AbstractAnimal(String name, String species) {
        this.name = name;
        this.species = species;
    }
    
    @Override
    public String getInfo() {
        return name + " is a " + species;
    }
}

class Dog extends AbstractAnimal {
    private String breed;
    
    public Dog(String name, String breed) {
        super(name, "Dog");
        this.breed = breed;
    }
    
    @Override
    public String makeSound() {
        return "Woof!";
    }
    
    @Override
    public String getInfo() {
        return super.getInfo() + " of breed " + breed;
    }
}

public class Main {
    public static void main(String[] args) {
        Dog dog = new Dog("Buddy", "Golden Retriever");
        System.out.println(dog.getInfo());
        System.out.println(dog.name + " says: " + dog.makeSound());
    }
}''',
                },
                'example': '''// Example: Calculate factorial
public class Main {
    public static void main(String[] args) {
        int number = 5;
        long result = factorial(number);
        System.out.println("Factorial of " + number + " is " + result);
    }
    
    public static long factorial(int n) {
        if (n <= 1) {
            return 1;
        }
        return n * factorial(n - 1);
    }
}'''
            }
        }
    
    def execute_python_safe(self, code):
        """Execute Python code in a safe environment"""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Safe globals with common functions
            safe_globals = {
                '__name__': '__main__',
                '__file__': '<string>',
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'sum': sum,
                    'max': max,
                    'min': min,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'reversed': reversed,
                    'type': type,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'bool': bool,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                }
            }
            
            exec(code, safe_globals)
            
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            if stderr_output:
                return False, stderr_output
            
            return True, stdout_output
            
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            return False, f"Error: {str(e)}"
    
    def execute_java_code(self, code):
        """Execute Java code with compilation step"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract class name from code
                class_match = re.search(r'public class (\w+)', code)
                if not class_match:
                    return False, "Error: No public class found. Java code must contain a public class."
                
                class_name = class_match.group(1)
                java_file = os.path.join(temp_dir, f"{class_name}.java")
                
                # Write Java code to file
                with open(java_file, 'w') as f:
                    f.write(code)
                
                # Compile Java code
                compile_result = subprocess.run(
                    ['javac', java_file],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=temp_dir
                )
                
                if compile_result.returncode != 0:
                    return False, f"Compilation Error:\n{compile_result.stderr}"
                
                # Run Java code
                run_result = subprocess.run(
                    ['java', class_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=temp_dir
                )
                
                if run_result.returncode != 0:
                    return False, f"Runtime Error:\n{run_result.stderr}"
                
                return True, run_result.stdout
                
        except subprocess.TimeoutExpired:
            return False, "Error: Code execution timed out"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def execute_code(self, code, language):
        """Main method to execute code based on language"""
        if language not in self.supported_languages:
            return False, f"Language '{language}' not supported"
        
        if not code or not code.strip():
            return False, "No code provided"
        
        if language == 'python':
            return self.execute_python_safe(code)
        elif language == 'java':
            return self.execute_java_code(code)
        else:
            return False, f"Language '{language}' is not supported"

def display_simple_ide():
    """Display the simplified IDE interface"""
    # Add sidebar with navigation
    with st.sidebar:
        # Display logo centered
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style='text-align: center;'>
                <img src="data:image/jpg;base64,{}" 
                     style='width: 300px; height: 300px; object-fit: contain;'/>
            </div>
            """.format(
                __import__('base64').b64encode(open("assets/FullLogo.jpg", "rb").read()).decode()
            ), unsafe_allow_html=True)
        st.markdown("---")
        
        if st.button("🏠 Back to Home", use_container_width=True):
            utils.go_to_page("landing")
    
    st.title("💻 Code Playground")
    st.markdown("*Interactive Python and Java Development Environment*")
    
    # Demo disclaimer
    st.info("""
    🎯 **Demo Feature Notice**
    
    This code playground is for demonstration purposes only. In the full version, Lola will:
    1. Assess your coding skill level through interactive exercises
    2. Create personalized learning projects based on your experience
    3. Provide real-time feedback and guidance
    4. Track your progress and suggest appropriate challenges
    
    For now, feel free to explore the example code samples below!
    """)
    
    # Initialize executor
    if 'simple_executor' not in st.session_state:
        st.session_state.simple_executor = SimpleCodeExecutor()
    
    executor = st.session_state.simple_executor
    
    # Initialize language-specific code storage
    if 'language_code' not in st.session_state:
        st.session_state.language_code = {
            'python': executor.supported_languages['python']['examples']['beginner'],
            'java': executor.supported_languages['java']['examples']['beginner']
        }
    
    # Language selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Choose Programming Language")
        selected_language = st.selectbox(
            "Select language:",
            options=list(executor.supported_languages.keys()),
            format_func=lambda x: x.title()
        )
    
    with col2:
        st.markdown("### Code Samples")
        difficulty = st.selectbox(
            "Select difficulty:",
            options=['beginner', 'intermediate', 'advanced'],
            format_func=lambda x: x.title()
        )
        if st.button("Load Sample", type="secondary"):
            st.session_state.language_code[selected_language] = executor.supported_languages[selected_language]['examples'][difficulty]
            st.rerun()
    
    # Code input area
    st.markdown("### Write Your Code")
    
    code_input = st.text_area(
        f"Enter your {selected_language.title()} code:",
        value=st.session_state.language_code[selected_language],
        height=300,
        key="simple_code_editor",
        help=f"Write {selected_language} code here. Use Ctrl+Enter to run."
    )
    
    # Update session state when code changes
    st.session_state.language_code[selected_language] = code_input
    
    # Execution controls
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        run_button = st.button("▶️ Run Code", type="primary")
    
    with col2:
        clear_button = st.button("🗑️ Clear")
        if clear_button:
            st.session_state.language_code[selected_language] = ""
            st.rerun()
    
    # Code execution
    if run_button and code_input.strip():
        with st.spinner(f"Executing {selected_language} code..."):
            success, output = executor.execute_code(code_input, selected_language)
        
        # Display results
        st.markdown("### Output")
        
        if success:
            if output.strip():
                st.success("Code executed successfully!")
                st.code(output, language="text")
            else:
                st.success("Code executed successfully! (No output)")
        else:
            st.error("Code execution failed!")
            st.code(output, language="text")
            
            # Show basic error suggestions
            if not success:
                st.markdown("### 💡 Tips")
                if selected_language == 'java':
                    if "class" in output.lower() and "not found" in output.lower():
                        st.info("Make sure your class name matches the filename and is public.")
                    elif "compilation" in output.lower():
                        st.info("Check your Java syntax - semicolons, brackets, and method declarations.")
                elif selected_language == 'python':
                    if "syntax" in output.lower():
                        st.info("Check your Python syntax - indentation, colons, and parentheses.")
                    elif "name" in output.lower() and "not defined" in output.lower():
                        st.info("Make sure all variables are defined before use.")
    
    # Language information
    st.markdown("---")
    st.markdown("### 📚 Language Support")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Python Features:**
        - Safe execution environment
        - Built-in functions available
        - Real-time error feedback
        - Educational examples
        """)
    
    with col2:
        st.markdown("""
        **Java Features:**
        - Full compilation cycle
        - Class-based execution
        - Automatic class detection
        - Compilation error reporting
        """)