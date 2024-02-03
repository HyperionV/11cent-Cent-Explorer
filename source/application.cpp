#include "application.hpp"

Application::Application() : width(1280), height(720), fps(60), title("Application") {
	InitWindow(width, height, title.c_str());
	SetTargetFPS(fps);
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
	while(!WindowShouldClose()) {
		BeginDrawing();
		ClearBackground(RAYWHITE);
		EndDrawing();
	}
}

Application* Application::_instance = nullptr;