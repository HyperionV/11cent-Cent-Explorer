#ifndef BOX_HPP_
#define BOX_HPP_

#include <iostream>
#include <string>

#include "raylib.h"
#include "theme.hpp"
#include "object.hpp"

class Box : public Object {
protected:
	Color color = theme::foreground;

public:
	using Object::Object;
	Box(Rectangle rec, Color color);

	void draw();
};

#endif // BOX_HPP