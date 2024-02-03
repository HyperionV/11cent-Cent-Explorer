#include "application.hpp"

Application::Application() : width(1280), height(720), fps(60), title("Cent Explorer") {
	InitWindow(width, height, title.c_str());
	SetTargetFPS(fps);

	registry = SceneRegistry::instance();
	scene = registry->scene(SceneID::MENU);
}

Application::~Application() {
	CloseWindow();
	if(_instance) delete _instance;
}

Application* Application::instance() {
	if(!_instance) _instance = new Application();
	return _instance;
}

void Application::run() {
	while(!WindowShouldClose() && scene) {
		BeginDrawing();
		ClearBackground(RAYWHITE);
		scene->draw();
		EndDrawing();
		
		scene = scene->update();
	}
}

Application* Application::_instance = nullptr;