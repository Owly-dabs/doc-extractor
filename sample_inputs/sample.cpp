// Adds two integers
// Returns the sum of a and b
// Example usage:
// int result = add(3, 4); // result will be 7
// Note: This function does not handle overflow.
// It is intended for educational purposes only.
// This function is part of a sample C++ project demonstrating docstring parsing.
int add(int a, int b) {
    return a + b;
}

/** Represents a user. */
class User {
    /** The user's ID. */
    int id;

    /** Returns the user ID. */
    int getId() const {
        return id;
    }
};