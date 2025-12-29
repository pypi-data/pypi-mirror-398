#include <pybind11/pybind11.h>
#include <pybind11/stl.h>   // so std::vector<Event> becomes a Python list

#include "engine.h"

namespace py = pybind11;

PYBIND11_MODULE(_native, m) {
    m.doc() = "Mini arcade native SDL2 backend";

    // Bind the EventType enum
    py::enum_<mini::EventType>(m, "EventType")
        .value("Unknown", mini::EventType::Unknown)
        .value("Quit", mini::EventType::Quit)
        .value("KeyDown", mini::EventType::KeyDown)
        .value("KeyUp", mini::EventType::KeyUp)
        .value("MouseMotion", mini::EventType::MouseMotion)
        .value("MouseButtonDown", mini::EventType::MouseButtonDown)
        .value("MouseButtonUp", mini::EventType::MouseButtonUp)
        .value("MouseWheel", mini::EventType::MouseWheel)
        .value("WindowResized", mini::EventType::WindowResized)
        .value("TextInput", mini::EventType::TextInput)
        .export_values();

    // Bind the Event struct
    py::class_<mini::Event>(m, "Event")
        .def_readonly("type", &mini::Event::type)
        .def_readonly("key", &mini::Event::key)
        .def_readonly("scancode", &mini::Event::scancode)
        .def_readonly("mod", &mini::Event::mod)
        .def_readonly("repeat", &mini::Event::repeat)
        .def_readonly("x", &mini::Event::x)
        .def_readonly("y", &mini::Event::y)
        .def_readonly("dx", &mini::Event::dx)
        .def_readonly("dy", &mini::Event::dy)
        .def_readonly("button", &mini::Event::button)
        .def_readonly("wheel_x", &mini::Event::wheel_x)
        .def_readonly("wheel_y", &mini::Event::wheel_y)
        .def_readonly("width", &mini::Event::width)
        .def_readonly("height", &mini::Event::height)
        .def_readonly("text", &mini::Event::text);

    // Bind the Engine class
    py::class_<mini::Engine>(m, "Engine")
        .def(py::init<>())
        .def("init", &mini::Engine::init,
                py::arg("width"), py::arg("height"), py::arg("title"))

        .def("set_clear_color", &mini::Engine::set_clear_color,
                py::arg("r"), py::arg("g"), py::arg("b"))

        .def("begin_frame", &mini::Engine::begin_frame)
        .def("end_frame", &mini::Engine::end_frame)

        .def("draw_rect", &mini::Engine::draw_rect,
                py::arg("x"), py::arg("y"),
                py::arg("w"), py::arg("h"),
                py::arg("r"), py::arg("g"), py::arg("b"), py::arg("a"))

        .def("draw_sprite", &mini::Engine::draw_sprite,
                py::arg("texture_id"), py::arg("x"), py::arg("y"),
                py::arg("w"), py::arg("h"))

        .def("load_font", &mini::Engine::load_font,
                py::arg("path"), py::arg("pt_size"))

        .def(
            "draw_text",
            &mini::Engine::draw_text,
                py::arg("text"),
                py::arg("x"),
                py::arg("y"),
                py::arg("r"),
                py::arg("g"),
                py::arg("b"),
                py::arg("a"),
                py::arg("font_id") = -1
        )
        .def("poll_events", &mini::Engine::poll_events)

        .def("capture_frame", &mini::Engine::capture_frame,
                py::arg("path"))
        .def(
        "measure_text",
                &mini::Engine::measure_text,
                py::arg("text"),
                py::arg("font_id") = -1
        );
}
