#ifndef APPLICATION_HPP
#define APPLICATION_HPP

#include <iostream>
#include <string>

#include "raylib.h"
#include "raygui.h"
#include "scene_registry.hpp"

class Application {
private:
	static Application* _instance;

	std::string title;
	int width, height, fps;

	SceneRegistry* registry;
	Scene* scene;

	Application();
	~Application();

public:
	Application(const Application&) = delete;
	Application& operator=(const Application&) = delete;
	Application(Application&&) = delete;

	static Application* instance();
	void run();
};

#endif // APPLICATION_HPP