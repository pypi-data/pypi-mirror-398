#include "common/binary_indexed_tree.h"

#include <ranges>
#include <algorithm>
using namespace std;
using namespace graph_layout;

BinaryIndexedTree::BinaryIndexedTree(const size_t n) : _bit(n + 1) {}

/** Find the next index for a binary indexed tree.
 *
 * @param index Current index.
 * @return The offset for the next index.
 */
int BinaryIndexedTree::next(const int index) {
    return index & -index;
}

void BinaryIndexedTree::add(int index, const int val) {
    ++index;
    while (index < static_cast<int>(_bit.size())) {
        _bit[index] += val;
        index += next(index);
    }
}

long long BinaryIndexedTree::prefixSum(int index) const {
    long long sum = 0;
    ++index;
    while (index > 0) {
        sum += _bit[index];
        index -= next(index);
    }
    return sum;
}

void BinaryIndexedTree::clear() {
    ranges::fill(_bit, 0);
}

void BinaryIndexedTree::clear(const size_t n) {
    if (n + 1 < _bit.size()) {
        fill(_bit.begin(), _bit.begin() + static_cast<int>(n) + 1, 0);
    } else {
        clear();
    }
}
