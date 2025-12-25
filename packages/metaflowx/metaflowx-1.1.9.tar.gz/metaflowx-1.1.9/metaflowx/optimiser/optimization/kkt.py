def kkt(vars, f, g_list=None, h_list=None, minimize=True):
    """
    Solve constrained optimization problems using Karush–Kuhn–Tucker (KKT) conditions.
    Prints a detailed, exam-style, step-by-step derivation.

    Parameters
    ----------
    vars : list of sympy symbols
        Decision variables, e.g. [x, y]
    f : sympy expression
        Objective function f(x)
    g_list : list of sympy expressions
        Inequality constraints g_i(x) ≤ 0
    h_list : list of sympy expressions
        Equality constraints h_j(x) = 0
    minimize : bool
        If True, treat as minimization (default).
        If False, treat as maximization (internally minimize -f).


    Examples
    --------
    >>> import sympy as sp
    >>> # Define variables
    >>> x, y = sp.symbols('x y', real=True)

    >>> # Objective
    >>> f = (x-1)**2 + (y-2)**2

    >>> # Constraints
    >>> g = [2 - x - y, 1 - x]  #These are the inequality constraints
    >>> h = [] # Equality constraints

    >>> kkt([x, y], f, g_list=g, h_list=h)
    """

    # ----------------------------------------------------------
    # Normalization and helpers
    # ----------------------------------------------------------
    g = g_list if g_list else []
    h = h_list if h_list else []

    # If it's a maximization, convert to minimizing -f
    if not minimize:
        f_eff = -f
    else:
        f_eff = f

    def big(title: str):
        print("\n" + title)
        print("=" * len(title))

    def sub(title: str):
        print("\n" + title)
        print("-" * len(title))

    def expr(e):
        return sp.simplify(e)

    # ----------------------------------------------------------
    # 0. Theoretical KKT template (like writing theory in exam)
    # ----------------------------------------------------------
    big("GENERAL KKT CONDITIONS (THEORY)")

    print("Consider the nonlinear programming problem:")
    print("  Minimize   f(x)")
    print("  subject to g_i(x) ≤ 0,   i = 1, ..., m")
    print("             h_j(x) = 0,   j = 1, ..., p")

    print("\nThe Karush–Kuhn–Tucker (KKT) conditions at a point x* with multipliers λᵢ, μⱼ are:")
    print("  1) Stationarity:")
    print("       ∇f(x*) + Σ λᵢ ∇gᵢ(x*) + Σ μⱼ ∇hⱼ(x*) = 0")
    print("  2) Primal feasibility:")
    print("       gᵢ(x*) ≤ 0,   hⱼ(x*) = 0")
    print("  3) Dual feasibility:")
    print("       λᵢ ≥ 0  for all i")
    print("  4) Complementary slackness:")
    print("       λᵢ gᵢ(x*) = 0  for all i")

    # ----------------------------------------------------------
    # 1. Problem statement for this specific problem
    # ----------------------------------------------------------
    big("GIVEN PROBLEM (SPECIFIC DATA)")

    print("\nDecision variables:")
    print("  x =", ", ".join(str(v) for v in vars))

    if minimize:
        print("\nObjective:  Minimize  f(x)")
    else:
        print("\nObjective:  Maximize  f(x)")
        print("Note: To apply KKT, we equivalently minimize  f_eff(x) = -f(x).")

    print("\nObjective function:")
    print("  f(x)  =", expr(f))
    if not minimize:
        print("  Effective function used for KKT (to minimize):")
        print("  f_eff(x) = -f(x) =", expr(f_eff))

    print("\nInequality constraints  gᵢ(x) ≤ 0:")
    if not g:
        print("  (No inequality constraints)")
    else:
        for i, gi in enumerate(g, 1):
            print(f"  g{i}(x) =", expr(gi), "≤ 0")

    print("\nEquality constraints  hⱼ(x) = 0:")
    if not h:
        print("  (No equality constraints)")
    else:
        for j, hj in enumerate(h, 1):
            print(f"  h{j}(x) =", expr(hj), "= 0")

    # ----------------------------------------------------------
    # 2. Lagrangian
    # ----------------------------------------------------------
    big("LAGRANGIAN FUNCTION")

    m = len(g)
    p = len(h)

    lambdas = sp.symbols(f"λ1:{m+1}", real=True) if m > 0 else []
    mus     = sp.symbols(f"μ1:{p+1}", real=True) if p > 0 else []

    L = f_eff \
        + sum(lambdas[i] * g[i] for i in range(m)) \
        + sum(mus[j] * h[j] for j in range(p))

    print("\nGeneral form of the Lagrangian:")
    print("  L(x, λ, μ) = f_eff(x) + Σ λᵢ gᵢ(x) + Σ μⱼ hⱼ(x)")
    print("\nFor this particular problem:")
    print("  L(x, λ, μ) =", expr(L))

    # ----------------------------------------------------------
    # 3. Gradients of f, gᵢ, hⱼ (optional, but exam-style)
    # ----------------------------------------------------------
    big("GRADIENTS OF OBJECTIVE AND CONSTRAINTS")

    print("\nGradient of f_eff(x):")
    for v in vars:
        print(f"  ∂f_eff/∂{v} =", expr(sp.diff(f_eff, v)))

    if m > 0:
        print("\nGradients of inequality constraints gᵢ(x):")
        for i, gi in enumerate(g, 1):
            print(f"  ∇g{i}(x):")
            for v in vars:
                print(f"    ∂g{i}/∂{v} =", expr(sp.diff(gi, v)))
    else:
        print("\nNo inequality constraints gᵢ(x).")

    if p > 0:
        print("\nGradients of equality constraints hⱼ(x):")
        for j, hj in enumerate(h, 1):
            print(f"  ∇h{j}(x):")
            for v in vars:
                print(f"    ∂h{j}/∂{v} =", expr(sp.diff(hj, v)))
    else:
        print("\nNo equality constraints hⱼ(x).")

    # ----------------------------------------------------------
    # 4. Stationarity: ∇ₓL = 0
    # ----------------------------------------------------------
    big("STATIONARITY CONDITION  (∇ₓL = 0)")

    stationarity_eqs = []
    print("\nCompute partial derivatives of L with respect to each variable and set to zero:")
    for v in vars:
        dLdv = sp.diff(L, v)
        stationarity_eqs.append(sp.Eq(dLdv, 0))
        print(f"  ∂L/∂{v} =", expr(dLdv), "= 0")

    # ----------------------------------------------------------
    # 5. Complementary slackness λᵢ gᵢ(x*) = 0
    # ----------------------------------------------------------
    big("COMPLEMENTARY SLACKNESS  (λᵢ gᵢ(x*) = 0)")

    cs_eqs = []
    if m == 0:
        print("There are no inequality constraints ⇒ no complementary slackness equations.")
    else:
        print("For each inequality constraint gᵢ(x) ≤ 0 we have:")
        for i, gi in enumerate(g, 1):
            eq = sp.Eq(lambdas[i-1] * gi, 0)
            cs_eqs.append(eq)
            print(f"  λ{i} * g{i}(x) = 0")

    # ----------------------------------------------------------
    # 6. Primal & Dual feasibility (as conditions, not solved yet)
    # ----------------------------------------------------------
    big("PRIMAL AND DUAL FEASIBILITY (CONDITION STATEMENT)")

    print("\nPrimal feasibility requires:")
    if m > 0:
        for i in range(1, m+1):
            print(f"  g{i}(x*) ≤ 0")
    else:
        print("  (No gᵢ constraints)")

    if p > 0:
        for j in range(1, p+1):
            print(f"  h{j}(x*) = 0")
    else:
        print("  (No hⱼ constraints)")

    print("\nDual feasibility requires:")
    if m > 0:
        for i in range(1, m+1):
            print(f"  λ{i} ≥ 0")
    else:
        print("  (No λᵢ multipliers, since no inequality constraints)")

    # ----------------------------------------------------------
    # 7. Build and solve algebraic KKT system
    # ----------------------------------------------------------
    big("ALGEBRAIC KKT SYSTEM (EQUATIONS TO SOLVE)")

    all_eqs = stationarity_eqs + cs_eqs + [sp.Eq(hj, 0) for hj in h]
    unknowns = list(vars) + list(lambdas) + list(mus)

    print("\nCollecting all equations from stationarity,")
    if m > 0:
        print("complementary slackness,")
    if p > 0:
        print("and equality constraints hⱼ(x) = 0:")
    print()

    for eq in all_eqs:
        lhs = expr(eq.lhs)
        rhs = expr(eq.rhs)
        print(" ", lhs, "=", rhs)

    print("\nWe now solve this system symbolically for the unknowns (x*, λ*, μ*):")
    solutions = sp.solve(all_eqs, unknowns, dict=True)

    if not solutions:
        print("\nNo symbolic solutions to the KKT system were found.")
        return

    # ----------------------------------------------------------
    # 8. List raw KKT candidate points
    # ----------------------------------------------------------
    big("KKT CANDIDATE POINTS (RAW SOLUTIONS OF THE SYSTEM)")

    for idx, sol in enumerate(solutions, 1):
        print(f"\nCandidate {idx}:")
        for v in unknowns:
            if v in sol:
                print(f"  {v} =", expr(sol[v]))

    # ----------------------------------------------------------
    # 9. Feasibility + Interpretation (active/inactive)
    # ----------------------------------------------------------
    big("CHECK PRIMAL/DUAL FEASIBILITY AND INTERPRETATION")

    feasible_candidates = []

    for idx, sol in enumerate(solutions, 1):
        print(f"\nCandidate {idx}:")
        ok = True

        # Check each inequality constraint
        if m > 0:
            print("  Inequality constraints gᵢ(x*) ≤ 0 :")
        for i, gi in enumerate(g, 1):
            gi_val = expr(gi.subs(sol))

            try:
                gi_num = float(gi_val)   # force numeric conversion
            except:
                 gi_num = sp.N(gi_val)    # symbolic fallback

            print(f"    g{i}(x*) = {gi_val} ≈ {gi_num}")

            # Only compare if numeric
            if isinstance(gi_num, (int, float)):
                if gi_num > 1e-8:
                     print(f"      ⇒ Violates g{i}(x*) ≤ 0 → candidate not feasible.")
                     ok = False
                else:
                    if abs(gi_num) < 1e-8:
                         print(f"      ⇒ Constraint g{i} ACTIVE.")
                    else:
                         print(f"      ⇒ Constraint g{i} INACTIVE.")
            else:
                print(f"      ⇒ Cannot numerically determine feasibility for g{i}.")


        # Check equality constraints exactly
        if p > 0:
            print("  Equality constraints hⱼ(x*) = 0 :")
        for j, hj in enumerate(h, 1):
            hj_val = expr(hj.subs(sol))
            hj_num = sp.N(hj_val)
            print(f"    h{j}(x*) = {hj_val} ≈ {hj_num}")
            if abs(hj_num) > 1e-8:
                print(f"      ⇒ Violates h{j}(x*) = 0 → candidate not feasible.")
                ok = False

        # Check dual feasibility (λᵢ ≥ 0)
        if m > 0:
            print("  Dual feasibility (λᵢ ≥ 0):")
        for i, lam in enumerate(lambdas, 1):
            lam_val = sol.get(lam, None)
            if lam_val is None:
                print(f"    λ{i} is free / undetermined.")
                continue
            lam_num = sp.N(lam_val)
            print(f"    λ{i} = {lam_val} ≈ {lam_num}")
            if lam_num < -1e-8:
                print(f"      ⇒ Violates λ{i} ≥ 0 → candidate not feasible.")
                ok = False

        # Check complementary slackness numerically as a sanity check
        if m > 0:
            print("  Complementary slackness λᵢ gᵢ(x*):")
        for i, gi in enumerate(g, 1):
            if m == 0:
                break
            lam = lambdas[i-1]
            lam_val = sol.get(lam, 0)
            prod_val = expr(lam_val * gi.subs(sol))
            prod_num = sp.N(prod_val)
            print(f"    λ{i} * g{i}(x*) = {prod_val} ≈ {prod_num}")

        if ok:
            print("  ⇒ This candidate satisfies all KKT conditions (KKT-feasible).")
            feasible_candidates.append(sol)
        else:
            print("  ⇒ This candidate is NOT KKT-feasible.")

    # ----------------------------------------------------------
    # 10. Evaluate objective at feasible KKT points
    # ----------------------------------------------------------
    big("EVALUATION OF OBJECTIVE AT FEASIBLE KKT POINTS")

    if not feasible_candidates:
        print("\nNo KKT-feasible candidates were found.")
        return

    values = []
    for idx, sol in enumerate(feasible_candidates, 1):
        f_val = expr(f.subs(sol))
        f_num = sp.N(f_val)
        print(f"\nFeasible candidate {idx}:")
        for v in vars:
            print(f"  {v}* =", expr(sol[v]))
        print("  f(x*) =", f_val, "≈", f_num)
        values.append((f_num, sol))

    # ----------------------------------------------------------
    # 11. Identify best candidate (min or max)
    # ----------------------------------------------------------
    if minimize:
        big("FINAL ANSWER: CANDIDATE MINIMUM")
        best = min(values, key=lambda t: t[0])
    else:
        big("FINAL ANSWER: CANDIDATE MAXIMUM")
        best = max(values, key=lambda t: t[0])

    best_val, best_sol = best

    print("\nOptimal KKT candidate (based on objective value among feasible KKT points):")
    for v in vars:
        print(f"  {v}* =", expr(best_sol[v]))
    print("\nObjective value at this point:")
    print("  f(x*) =", expr(f.subs(best_sol)), "≈", best_val)

    # ----------------------------------------------------------
    # 12. Convexity / Hessian discussion (exam-style theory)
    # ----------------------------------------------------------
    big("CONVEXITY / SECOND-ORDER DISCUSSION (THEORETICAL JUSTIFICATION)")

    print("\nHessian of the effective objective f_eff(x):")
    H = sp.hessian(f_eff, vars)
    print("  H(x) =")
    print(H)

    try:
        eigenvals = H.eigenvals()
        print("\nEigenvalues of H(x) (symbolic, may depend on x):")
        for val, mult in eigenvals.items():
            print("  eigenvalue =", expr(val), " (multiplicity", mult, ")")
        print("\nIf all eigenvalues are ≥ 0 for all x, f_eff is convex.")
        print("If all eigenvalues are > 0 for all x, f_eff is strictly convex.")
    except Exception:
        print("\nCould not compute symbolic eigenvalues of the Hessian.")
        print("For numerical problems, evaluate H at specific points to check positive (semi)definiteness.")

    # Check whether all constraints are affine (linear) for convexity reasoning
    all_affine = True
    for gi in g:
        if sp.total_degree(gi) > 1:
            all_affine = False
    for hj in h:
        if sp.total_degree(hj) > 1:
            all_affine = False

    if all_affine:
        print("\nAll constraints gᵢ, hⱼ are affine (linear) in x.")
        print("Hence the feasible set is convex.")
        print("If f_eff is convex, any KKT-feasible point is a global optimum.")
    else:
        print("\nSome constraints are nonlinear, so the problem may be non-convex.")
        print("In that case, KKT-feasible points are candidates for local optima.")

    print("\nIn an exam, you would usually add a final sentence like:")
    if minimize:
        print("  “Therefore, the point found above is the (local/global) minimizer of f(x) subject to the given constraints.”")
    else:
        print("  “Therefore, the point found above is the (local/global) maximizer of f(x) subject to the given constraints.”")