# The O(n log n) Barrier

**Coding Temple AI Bootcamp · Module 2 · Time Complexity**
Author: Kathy Matos

## Why is O(n log n) the lower bound for comparison-based sorting?

Comparison-based sorting algorithms (merge sort, quicksort, heap sort) determine order by asking one question: "is `a` less than `b`?" Each comparison gives one bit of information. The proof that you can't beat O(n log n) is information-theoretic: there are `n!` possible orderings of `n` distinct items, and a binary decision tree distinguishing among them must have at least `n!` leaves. A binary tree with `n!` leaves has depth at least `log2(n!)`, which by Stirling's approximation is about `n log n`. So any algorithm that sorts purely by comparing pairs of items must make at least `O(n log n)` comparisons in the worst case — it's not about cleverness, it's about how much information each comparison gives you.

In practice, this means that for general sorting (arbitrary types, arbitrary comparators), `n log n` is as fast as you can go. Python's built-in `sorted()` and `list.sort()` use Timsort, which hits this bound and adds optimizations for partially-sorted data, but the asymptotic ceiling stands.

**You can sort faster than O(n log n) — but only by changing the rules.** If the items are not arbitrary (e.g., they're integers within a known range), you can replace comparisons with direct addressing or radix manipulation. That's a different model of computation, not a faster comparison sort.

## Bonus — Counting sort and radix sort

**Counting sort** runs in `O(n + k)`, where `k` is the range of input values. Instead of comparing items, it counts occurrences of each value in an array indexed by value, then reconstructs the sorted output. It beats `O(n log n)` when `k` is small relative to `n` — for example, sorting student exam scores (0-100) for a class of 10,000: `k=101`, `n=10,000`, so total work is `~10,100` operations vs `~133,000` for a comparison sort.

**Radix sort** is `O(d * (n + k))`, where `d` is the number of digits and `k` is the base (usually 10 or 256). Useful for sorting fixed-width integers, dates, or string keys of bounded length. The classic use case is sorting telephone numbers, ZIP codes, or IP addresses where you know the structure in advance.

The catch is that both rely on the input fitting a predictable structure. They aren't useful for sorting arbitrary objects with custom comparators (e.g., "sort these student records by GPA then by last name"). For that, you're back in comparison-sort land and stuck at `O(n log n)`.

In Caduceus terms: if you wanted to sort 100,000 edgar_observations rows by `period_end` (a fixed-format date), radix sort would beat Timsort. If you wanted to sort the same rows by a custom multi-key analyst preference (e.g., ticker alphabetical, then period descending, then concept by analytical priority), Timsort is what you'd use.
