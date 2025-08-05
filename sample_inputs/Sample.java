package sample_inputs;

// This class represents a sample.
// It is used to demonstrate how to write a simple Java class with a constructor and a method.
// The class has a single field, 'name', which is initialized through the constructor.
public class Sample {

    /** The sample's name. */
    private String name;

    /** Creates a new sample. */
    public Sample(String name) {
        this.name = name;
    }

    /** Returns the sample's name. */
    public String getName() {
        return name;
    }
}