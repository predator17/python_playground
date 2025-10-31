# ----------------------------------------------------
# 1. Global (G) Scope
# ----------------------------------------------------
X = "Global X (G): Defined in module scope."


def outer_func():
    # 2. Enclosing (E) Scope: The variable X we want to change
    X = "Enclosing X (E): Defined in outer_func."

    def inner_nonlocal_changer():
        # L-Scope: If X is assigned here, it is local by default [3].
        # However, we use 'nonlocal' to assign X in the closest enclosing scope [2, 4].
        nonlocal X
        X = "Nonlocal X (E-changed): Changed by inner_nonlocal_changer."
        print(f"L-Search: Inside changer: X is now changed via 'nonlocal'.")
        # When X is *referenced* here (e.g., in a print), the search stops at L, but since it was
        # just assigned via 'nonlocal', the L scope now has the new value inherited from E.

    # --- Execution within the Enclosing (E) Scope ---
    print(f"\n--- Starting Nonlocal Test inside {outer_func.__name__} ---")

    # Check E before call
    print(f"E-Scope Check (BEFORE NONLOCAL CALL): {X}")

    inner_nonlocal_changer()  # The nested function runs and uses 'nonlocal'

    # Check E after call: The E scope should now reflect the change made by the nested function.
    print(f"E-Scope Check (AFTER NONLOCAL CALL): {X}")

    # When Python resolves 'X' here, it finds it in its own scope (E).
    # This demonstrates that 'inner_nonlocal_changer' successfully modified the E scope [5].


# ----------------------------------------------------
# 4. Final Module Execution
# ----------------------------------------------------
outer_func()

# Access X at the top level (Global scope)
print("\nFinal Global Check: Outside all functions:", X)
