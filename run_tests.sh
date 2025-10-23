#!/bin/bash

# HumanEval Testing Suite - Comprehensive Test Runner
# Usage: ./run_tests.sh [options]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo ""
    echo "This script will:"
    echo "  1. Check for required files and environment"
    echo "  2. Generate permanent test runners for all LLM responses"
    echo "  3. Execute tests and show detailed individual results"
    echo "  4. Save comprehensive results to JSON file"
}

# Parse command line arguments
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Starting HumanEval LLM Response Testing Suite"
    echo "=============================================="
    
    # Check virtual environment
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found!"
        print_status "Run: ./setup.sh"
        exit 1
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Check required files
    if [ ! -f "setup_test.py" ]; then
        print_error "setup_test.py not found!"
        exit 1
    fi
    
    if [ ! -d "humaneval_problems" ]; then
        print_error "humaneval_problems directory not found!"
        print_status "Run: ./run.sh to download problems first"
        exit 1
    fi
    
    # Count problems and responses
    problem_count=$(find humaneval_problems -name "problem_*" -type d | wc -l | tr -d ' ')
    print_status "Found $problem_count problems"
    
    # Check for LLM response files
    declare -a found_responses=()
    for i in {1..10}; do  # Check up to 10 response files
        if find humaneval_problems -name "llm_response${i}.txt" -type f | grep -q .; then
            found_responses+=("llm_response${i}")
        fi
    done
    
    if [ ${#found_responses[@]} -eq 0 ]; then
        print_error "No llm_response*.txt files found!"
        print_status "Make sure you have llm_response1.txt, llm_response2.txt, etc. in your problem folders"
        exit 1
    fi
    
    print_status "Found LLM responses: ${found_responses[*]}"
    
    # Show what we're about to do
    echo ""
    print_status "Test Plan:"
    echo "  • Problems to test: $problem_count"
    echo "  • LLM responses: ${#found_responses[@]}"
    echo "  • Total test combinations: $((problem_count * ${#found_responses[@]}))"
    echo ""
    
    # Change to problems directory
    cd humaneval_problems
    
    # Run tests with optional verbose output
    print_status "Executing tests..."
    if [ "$VERBOSE" = true ]; then
        python ../setup_test.py
    else
        python ../setup_test.py 2>/dev/null
    fi
    
    test_exit_code=$?
    
    # Return to original directory
    cd ..
    
    # Show generated files
    print_status "Generated test files are kept for future reference:"
    find humaneval_problems -name "run_test_*.py" | head -5 | while read file; do
        echo "  • $file"
    done
    total_files=$(find humaneval_problems -name "run_test_*.py" | wc -l | tr -d ' ')
    if [ "$total_files" -gt 5 ]; then
        echo "  ... and $((total_files - 5)) more files"
    fi
    
    # Final status
    echo ""
    if [ $test_exit_code -eq 0 ]; then
        print_success "All tests completed successfully!"
    else
        print_warning "Some tests failed or encountered errors"
        print_status "Check the output above for details"
    fi
    
    echo ""
    print_status "Testing suite finished"
}

# Run main function
main "$@"