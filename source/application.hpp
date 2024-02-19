#ifndef APPLICATION_HPP_
#define APPLICATION_HPP_

#include <iostream>
#include <string>

#include "scene_registry.hpp"
#include "theme.hpp"

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