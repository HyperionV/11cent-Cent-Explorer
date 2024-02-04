#include "object.hpp"

Object::Object() : rec({ 0, 0, 0, 0 }), text("") {}
Object::Object(Rectangle rec, const char* text) : rec(rec), text(text) {}
Object::Object(Rectangle rec, const std::string &text) : rec(rec), text(text) {}