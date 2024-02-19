#include "box.hpp"

Box::Box(Rectangle rec, Color color) : Object(rec), color(color) {}

void Box::draw() {
	DrawRectangleRec(rec, color);
}
