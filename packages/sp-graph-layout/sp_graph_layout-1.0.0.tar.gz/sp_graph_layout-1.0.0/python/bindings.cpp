#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <memory>
#include "graph_layout.h"
#include "common/compare_svg.h"
using namespace std;
using namespace graph_layout;

namespace py = pybind11;

PYBIND11_MODULE(_core, m, py::mod_gil_not_used()) {
    m.def("_compare_svg", &_compareSVG);
    py::enum_<FeedbackArcsMethod>(m, "FeedbackArcsMethod")
        .value("EADES_93", FeedbackArcsMethod::EADES_93)
        .value("MIN_ID", FeedbackArcsMethod::MIN_ID)
        .export_values()
    ;
    py::enum_<LayerAssignmentMethod>(m, "LayerAssignmentMethod")
        .value("TOPOLOGICAL", LayerAssignmentMethod::TOPOLOGICAL)
        .value("MIN_NUM_OF_LAYERS", LayerAssignmentMethod::MIN_NUM_OF_LAYERS)
        .value("GANSNER_93", LayerAssignmentMethod::GANSNER_93)
        .value("MIN_TOTAL_EDGE_LENGTH", LayerAssignmentMethod::MIN_TOTAL_EDGE_LENGTH)
        .export_values()
    ;
    py::enum_<CrossMinimizationMethod>(m, "CrossMinimizationMethod")
        .value("BARYCENTER", CrossMinimizationMethod::BARYCENTER)
        .value("MEDIAN", CrossMinimizationMethod::MEDIAN)
        .value("PAIRWISE_SWITCH", CrossMinimizationMethod::PAIRWISE_SWITCH)
        .export_values()
    ;
    py::enum_<VertexPositioningMethod>(m, "VertexPositioningMethod")
        .value("BRANDES_KOPF", VertexPositioningMethod::BRANDES_KOPF)
        .export_values()
    ;
    py::class_<SPDirectedGraph, shared_ptr<SPDirectedGraph>>(m, "SPDirectedGraph")
        .def(py::init<size_t>(), py::arg("num_vertices"))
        .def("add_edge", py::overload_cast<int, int>(&SPDirectedGraph::addEdge), py::arg("u"), py::arg("v"))
        .def("add_edges", &SPDirectedGraph::addEdges, py::arg("edges"))
    ;
    py::class_<Attribute>(m, "Attribute")
        .def(py::init<>())
        .def("set", &Attribute::set)
        .def("value", &Attribute::value)
    ;
    py::class_<AttributeRankDir, Attribute>(m, "AttributeRankDir")
        .def(py::init<>())
        .def_property_readonly_static("TOP_TO_BOTTOM", [](py::object) { return AttributeRankDir::TOP_TO_BOTTOM; })
        .def_property_readonly_static("BOTTOM_TO_TOP", [](py::object) { return AttributeRankDir::BOTTOM_TO_TOP; })
        .def_property_readonly_static("LEFT_TO_RIGHT", [](py::object) { return AttributeRankDir::LEFT_TO_RIGHT; })
        .def_property_readonly_static("RIGHT_TO_LEFT", [](py::object) { return AttributeRankDir::RIGHT_TO_LEFT; })
    ;
    py::class_<AttributeShape, Attribute>(m, "AttributeShape")
        .def(py::init<>())
        .def_property_readonly_static("NONE", [](py::object) { return AttributeShape::NONE; })
        .def_property_readonly_static("CIRCLE", [](py::object) { return AttributeShape::CIRCLE; })
        .def_property_readonly_static("DOUBLE_CIRCLE", [](py::object) { return AttributeShape::DOUBLE_CIRCLE; })
        .def_property_readonly_static("ELLIPSE", [](py::object) { return AttributeShape::ELLIPSE; })
        .def_property_readonly_static("RECT", [](py::object) { return AttributeShape::RECT; })
    ;
    py::class_<Attributes>(m, "Attributes")
        .def(py::init<>())
        .def("set_rank_dir", &Attributes::setRankDir)
        .def("set_vertex_shape", &Attributes::setVertexShape)
    ;
    py::class_<DirectedGraphHierarchicalLayout>(m, "DirectedGraphHierarchicalLayout")
        .def(py::init<>())
        .def("create_graph", &DirectedGraphHierarchicalLayout::createGraph, py::arg("num_vertices"))
        .def("set_graph", &DirectedGraphHierarchicalLayout::setGraph, py::arg("graph"))
        .def("set_feedback_arcs_method", &DirectedGraphHierarchicalLayout::setFeedbackArcsMethod, py::arg("method"))
        .def("set_layer_assignment_method", &DirectedGraphHierarchicalLayout::setLayerAssignmentMethod, py::arg("method"))
        .def("set_cross_minimization_method", &DirectedGraphHierarchicalLayout::setCrossMinimizationMethod, py::arg("method"))
        .def("set_vertex_positioning_method", &DirectedGraphHierarchicalLayout::setVertexPositioningMethod, py::arg("method"))
        .def("set_vertex_labels", &DirectedGraphHierarchicalLayout::setVertexLabels, py::arg("labels"))
        .def("set_edge_label", &DirectedGraphHierarchicalLayout::setEdgeLabel, py::arg("edge_id"), py::arg("label"))
        .def("init_vertex_labels_with_numerical_values", py::overload_cast<int>(&DirectedGraphHierarchicalLayout::initVertexLabelsWithNumericalValues), py::arg("start") = 1)
        .def("attributes", &DirectedGraphHierarchicalLayout::attributes, py::return_value_policy::reference_internal)
        .def("layout_graph", &DirectedGraphHierarchicalLayout::layoutGraph)
        .def("render", py::overload_cast<>(&DirectedGraphHierarchicalLayout::render, py::const_))
        .def("to_svg", py::overload_cast<const string&>(&DirectedGraphHierarchicalLayout::render, py::const_), py::arg("file_path"))
    ;
}
