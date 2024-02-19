#ifndef OBJECT_HPP_
#define OBJECT_HPP_

#include <iostream>
#include <string>

#include "raylib.h"

class Object {
protected:
	Rectangle rec;

public:
	Object();
	Object(Rectangle rec);

	virtual void draw() = 0;
};

#endif // OBJECT_HPP_