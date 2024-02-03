#ifndef APPLICATION_HPP
#define APPLICATION_HPP

#include <iostream>
#include <string>

#include "raylib.h"
#include "raygui.h"

class Application {
private:
	static Application* _instance;

	std::string title;
	int width, height, fps;

	Application();
	~Application();

public:
	static Application* instance();
	void run();
};

#endif // APPLICATION_HPP