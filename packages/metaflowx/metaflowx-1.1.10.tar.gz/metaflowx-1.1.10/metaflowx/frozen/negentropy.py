def negentropy():
    """
    Prints a brief, notes-style explanation of Negentropy exactly the way it is
    described in ICA theory: definition, purpose, why it is used, and the common
    approximations. Short, crisp, exam-ready.
    """

    print("\n" + "="*90)
    print("NEGENTROPY — BRIEF ICA NOTES VERSION")
    print("="*90 + "\n")

    print("Negentropy is a measure of how far a random variable is from being Gaussian.")
    print("The idea is based on the fact that a Gaussian distribution has the maximum")
    print("entropy among all distributions with the same variance. Therefore:")
    print("\n    Negentropy J(Y) = H(Y_gaussian) - H(Y)\n")
    print("If J(Y) is large → Y is highly non-Gaussian, which is useful for ICA because")
    print("independent components must be non-Gaussian. ICA tries to maximize negentropy.")
    
    print("\nWhy use Negentropy?")
    print("Because it is a reliable measure of non-Gaussianity, and ICA relies on")
    print("non-Gaussianity to recover independent sources. Higher negentropy implies")
    print("greater structure, making separation easier.")

    print("\nApproximations used (because exact entropy is hard to compute):")
    print("  • Using kurtosis:   J(y) ≈ (1/12)(E[y³])² + (1/48)(kurtosis)²")
    print("  • Using non-quadratic functions G(y), such as:")
    print("        G1(y) = y^4   or")
    print("        G2(y) = log(cosh(y))")
    print("    Then:  J(y) ∝ (E[G(y)] - E[G(v)])²,  where v is standard Gaussian.")
    print("---------------------------------------------------")
    print("\nCommon good choices of G(y) used in ICA:")
    print("  • G1(y) = y^4")
    print("  • G2(y) = log(cosh(y))     (most popular, used in FastICA)")
    print("  • G3(y) = -exp(-y^2 / 2)")
    print("  • G4(y) = y * exp(-y^2 / 2)")
    print("  • G5(y) = y^3")
    print("These functions amplify non-Gaussian characteristics and provide stable")
    print("approximations to negentropy.")


    print("\nKey point:")
    print("Negentropy is always non-negative and becomes zero only for a pure Gaussian.")
    print("ICA maximizes negentropy to find the most non-Gaussian, and therefore most")
    print("independent, components.")

    print("\n" + "="*90)
    print("END OF NEGENTROPY NOTES")
    print("="*90 + "\n")
