def ica():
    """
    Conceptual demonstration of ICA fundamentals:
    - Mixing model
    - Independence assumption
    - Non-Gaussianity requirement
    - Ambiguities (scale, sign, order)
    - Simple example of mixed signals
    - Why Gaussian sources cannot be used
    """

    print("\n" + "-"*90)
    print("INTRODUCTION TO ICA (INDEPENDENT COMPONENT ANALYSIS)")
    print("-"*90)

    print(
        "\nICA tries to recover original independent source signals from observed mixtures. "
        "This is the classic 'cocktail party problem': several people talk simultaneously, "
        "microphones record mixed audio, and ICA attempts to separate the voices."
    )

    print("\nMixing model:  x = A s")
    print(
        "Here:\n"
        " - s = original independent sources\n"
        " - A = unknown mixing matrix\n"
        " - x = observed mixtures\n"
        "ICA tries to estimate W = A^-1 such that s ≈ W x.\n"
    )

    print("-"*90)
    print("TINY EXAMPLE OF MIXING")
    print("-"*90)

    print(
        "\nLet the original independent signals be:\n"
        "  s1(t) = speech from person 1\n"
        "  s2(t) = speech from person 2\n\n"
        "Suppose the mixing matrix is:\n"
        "  A = [[0.7, 0.3],\n"
        "       [0.4, 0.6]]\n\n"
        "Then the microphone recordings become:\n"
        "  x1(t) = 0.7*s1 + 0.3*s2\n"
        "  x2(t) = 0.4*s1 + 0.6*s2\n\n"
        "ICA sees ONLY x1 and x2, not A or the original s.\n"
    )

    print("-"*90)
    print("WHAT ICA ASSUMES")
    print("-"*90)

    print(
        "\nICA requires:\n"
        "  1. The sources must be statistically INDEPENDENT.\n"
        "  2. The sources must be NON-GAUSSIAN.\n"
        "Independence gives structure; non-Gaussianity gives a unique 'fingerprint' "
        "to detect each source."
    )

    print("-"*90)
    print("WHY ICA NEEDS NON-GAUSSIANITY (SUPER CLEAR EXPLANATION)")
    print("-"*90)

    print("\nIf the sources are Gaussian, ICA completely fails. Here's why:\n\n"
        "1. Gaussian distributions are perfectly 'smooth' and symmetric.\n"
        "   Any rotation of Gaussian sources gives another equally valid Gaussian representation.\n"
        "   ICA cannot tell which rotation is correct.\n\n"
        "2. All linear combinations of Gaussian variables are still Gaussian.\n"
        "   This destroys our ability to identify which combination corresponds to original sources.\n\n"
        "3. Gaussian signals have zero higher-order structure:\n"
        "      - Zero skewness\n"
        "      - Zero kurtosis\n"
        "      - All higher-order moments vanish\n"
        "   ICA needs these higher-order features to separate sources.\n\n"
        "Conclusion:\n"
        "  Gaussian sources have NO unique statistical signature,\n"
        "  so ICA has NO mathematical way to separate them."
    )

    print("-"*90)
    print("AMBIGUITIES IN ICA")
    print("-"*90)

    print(
        "\nEven after successful ICA separation, three ambiguities ALWAYS remain:\n\n"
        "1. SCALING AMBIGUITY:\n"
        "     If s is multiplied by k, A can be divided by k.\n"
        "     ICA cannot know the true scale of the source.\n\n"
        "2. SIGN AMBIGUITY:\n"
        "     s and -s are equally valid solutions.\n"
        "     ICA cannot know which is the 'correct' orientation.\n\n"
        "3. ORDER (PERMUTATION) AMBIGUITY:\n"
        "     ICA may output source #2 first and source #1 second.\n"
        "     Order of recovered signals is arbitrary.\n"
    )

    print("-"*90)
    print("SUMMARY OF ICA FUNDAMENTALS")
    print("-"*90)

    print(
        "\nICA solves x = A s by finding W such that s = W x consists of mutually "
        "independent, non-Gaussian signals. It uses independence and non-Gaussianity "
        "to reverse the mixing. ICA cannot be uniquely solved for Gaussian sources "
        "due to rotational symmetry. The separated signals are determined only up to "
        "scale, sign, and order.\n"
    )

    print("-"*90)
    print("END OF ICA EXPLANATION")
    print("-"*90)
