#include "application.hpp"

int main() {
	Application* app = Application::instance();
	app->run();
	return 0;
}