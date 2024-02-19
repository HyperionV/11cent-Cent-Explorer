#include "object.hpp"

Object::Object() : rec({ 0, 0, 0, 0 }) {}
Object::Object(Rectangle rec) : rec(rec) {}