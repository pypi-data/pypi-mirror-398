#ifndef GRAPHLAYOUT_BINARY_INDEXED_TREE_H
#define GRAPHLAYOUT_BINARY_INDEXED_TREE_H

#include <vector>

namespace graph_layout {

    class BinaryIndexedTree {
    public:
        explicit BinaryIndexedTree(size_t n);
        ~BinaryIndexedTree() = default;

        /** Add a number to a binary indexed tree.
         *
         * @param index The index to add the value.
         * @param val The value to add.
         */
        void add(int index, int val = 1);

        /** Get the prefix sum from a binary indexed tree.
         *
         * @param index The index of the last element, inclusive.
         * @return The prefix sum.
         */
        [[nodiscard]] long long prefixSum(int index) const;

        void clear();
        void clear(size_t n);

    private:
        std::vector<long long> _bit;

        static int next(int index);
    };

};

#endif //GRAPHLAYOUT_BINARY_INDEXED_TREE_H