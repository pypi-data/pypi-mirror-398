#include "engine.h"

#include <stdexcept>
#include <iostream>
#include <utility>
#include <cstring>

namespace mini {

    Engine::Engine()
        : window_(nullptr),
            renderer_(nullptr),
            initialized_(false),
            font_(nullptr),
            clear_color_{0, 0, 0, 255},
            default_font_id_(-1),
            default_alpha_(255)
    {
    }

    Engine::~Engine()
    {
        if (font_ != nullptr) {
            TTF_CloseFont(font_);
            font_ = nullptr;
        }

        if (renderer_ != nullptr) {
            SDL_DestroyRenderer(renderer_);
            renderer_ = nullptr;
        }

        if (window_ != nullptr) {
            SDL_DestroyWindow(window_);
            window_ = nullptr;
        }

        if (initialized_) {
            SDL_Quit();
            initialized_ = false;
        }

        for (TTF_Font* f : fonts_) {
            if (f) TTF_CloseFont(f);
        }
        fonts_.clear();

        TTF_Quit();
        SDL_StopTextInput();

    }

    void Engine::init(int width, int height, const char* title)
    {
        if (initialized_) {
            return; // already initialized
        }

        if (SDL_Init(SDL_INIT_VIDEO) != 0) {
            throw std::runtime_error(std::string("SDL_Init Error: ") + SDL_GetError());
        }

        if (TTF_Init() != 0) {
            std::string msg = std::string("TTF_Init Error: ") + TTF_GetError();
            SDL_Quit();
            throw std::runtime_error(msg);
        }

        window_ = SDL_CreateWindow(
            title,
            SDL_WINDOWPOS_CENTERED,
            SDL_WINDOWPOS_CENTERED,
            width,
            height,
            SDL_WINDOW_SHOWN
        );

        if (window_ == nullptr) {
            std::string msg = std::string("SDL_CreateWindow Error: ") + SDL_GetError();
            TTF_Quit();
            SDL_Quit();
            throw std::runtime_error(msg);
        }

        renderer_ = SDL_CreateRenderer(
            window_,
            -1,
            SDL_RENDERER_ACCELERATED
        );

        if (renderer_ == nullptr) {
            std::string msg = std::string("SDL_CreateRenderer Error: ") + SDL_GetError();
            SDL_DestroyWindow(window_);
            window_ = nullptr;
            TTF_Quit();
            SDL_Quit();
            throw std::runtime_error(msg);
        }

        // Enable alpha blending for RGBA drawing
        SDL_SetRenderDrawBlendMode(renderer_, SDL_BLENDMODE_BLEND);

        SDL_StartTextInput();   // <--- needed for SDL_TEXTINPUT

        initialized_ = true;
    }

    void Engine::set_clear_color(int r, int g, int b)
    {
        auto clamp = [](int v) {
            if (v < 0) return 0;
            if (v > 255) return 255;
            return v;
        };

        clear_color_.r = static_cast<Uint8>(clamp(r));
        clear_color_.g = static_cast<Uint8>(clamp(g));
        clear_color_.b = static_cast<Uint8>(clamp(b));
        clear_color_.a = 255;
    }

    void Engine::begin_frame()
    {
        if (!initialized_ || renderer_ == nullptr) {
            return;
        }

        // use stored clear color instead of hard-coded black
        SDL_SetRenderDrawColor(
            renderer_,
            clear_color_.r,
            clear_color_.g,
            clear_color_.b,
            clear_color_.a
        );
        SDL_RenderClear(renderer_);
    }

    void Engine::end_frame()
    {
        if (!initialized_ || renderer_ == nullptr) {
            return;
        }

        SDL_RenderPresent(renderer_);
    }

    void Engine::draw_rect(int x, int y, int w, int h, int r, int g, int b, int a)
    {
        if (!initialized_ || renderer_ == nullptr) {
            return;
        }

        auto clamp = [](int v) {
            if (v < 0) return 0;
            if (v > 255) return 255;
            return v;
        };

        SDL_Rect rect{ x, y, w, h };

        // alpha or default alpha
        a = (a < 0) ? default_alpha_ : a;

        SDL_SetRenderDrawColor(
            renderer_,
            static_cast<Uint8>(clamp(r)),
            static_cast<Uint8>(clamp(g)),
            static_cast<Uint8>(clamp(b)),
            static_cast<Uint8>(clamp(a))
        );
        SDL_RenderFillRect(renderer_, &rect);

    }

    void Engine::draw_sprite(int /*texture_id*/, int /*x*/, int /*y*/, int /*w*/, int /*h*/)
    {
        // TODO: placeholder for later texture management.
    }

    // Load a TTF font from file at specified point size.
    int Engine::load_font(const char* path, int pt_size)
    {
        if (!initialized_) {
            throw std::runtime_error("Engine::init must be called before load_font");
        }

        TTF_Font* f = TTF_OpenFont(path, pt_size);
        if (!f) {
            throw std::runtime_error(std::string("TTF_OpenFont Error: ") + TTF_GetError());
        }

        fonts_.push_back(f);
        int id = static_cast<int>(fonts_.size() - 1);

        // first loaded font becomes default (good default behavior)
        if (default_font_id_ < 0) {
            default_font_id_ = id;
        }

        return id;
    }

    // Draw text at specified position.
    void Engine::draw_text(const char* text, int x, int y, int r, int g, int b, int a, int font_id)
    {
        if (!initialized_ || renderer_ == nullptr) return;

        int idx = (font_id >= 0) ? font_id : default_font_id_;
        if (idx < 0 || idx >= (int)fonts_.size() || fonts_[idx] == nullptr) return;

        TTF_Font* font = fonts_[idx];

        auto clamp = [](int v) {
            if (v < 0) return 0;
            if (v > 255) return 255;
            return v;
        };


        // alpha or default alpha
        a = (a < 0) ? default_alpha_ : a;
        SDL_Color color = { (Uint8)clamp(r), (Uint8)clamp(g), (Uint8)clamp(b), static_cast<Uint8>(clamp(a)) };

        SDL_Surface* surface = TTF_RenderUTF8_Blended(font, text, color);
        if (!surface) {
            std::cerr << "TTF_RenderUTF8_Blended Error: " << TTF_GetError() << std::endl;
            return;
        }

        SDL_Texture* texture = SDL_CreateTextureFromSurface(renderer_, surface);
        if (!texture) {
            std::cerr << "SDL_CreateTextureFromSurface Error: " << SDL_GetError() << std::endl;
            SDL_FreeSurface(surface);
            return;
        }

        SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_BLEND);
        SDL_SetTextureAlphaMod(texture, static_cast<Uint8>(clamp(a)));

        SDL_Rect dstRect{ x, y, surface->w, surface->h };
        SDL_FreeSurface(surface);

        SDL_RenderCopy(renderer_, texture, nullptr, &dstRect);
        SDL_DestroyTexture(texture);
    }

    bool Engine::capture_frame(const char* path)
    {
        if (!initialized_ || renderer_ == nullptr) {
            return false;
        }

        int width = 0;
        int height = 0;
        if (SDL_GetRendererOutputSize(renderer_, &width, &height) != 0) {
            std::cerr << "SDL_GetRendererOutputSize Error: " << SDL_GetError() << std::endl;
            return false;
        }

        // Create a surface to hold the pixels (32-bit RGBA)
        SDL_Surface* surface = SDL_CreateRGBSurfaceWithFormat(
            0,
            width,
            height,
            32,
            SDL_PIXELFORMAT_ARGB8888
        );

        if (!surface) {
            std::cerr << "SDL_CreateRGBSurfaceWithFormat Error: " << SDL_GetError() << std::endl;
            return false;
        }

        // Read pixels from the current render target into the surface
        if (SDL_RenderReadPixels(
                renderer_,
                nullptr,                        // whole screen
                surface->format->format,
                surface->pixels,
                surface->pitch) != 0)
        {
            std::cerr << "SDL_RenderReadPixels Error: " << SDL_GetError() << std::endl;
            SDL_FreeSurface(surface);
            return false;
        }

        // Save as BMP (simple, no extra dependencies).
        // Use .bmp extension in the path you pass from Python.
        if (SDL_SaveBMP(surface, path) != 0) {
            std::cerr << "SDL_SaveBMP Error: " << SDL_GetError() << std::endl;
            SDL_FreeSurface(surface);
            return false;
        }

        SDL_FreeSurface(surface);
        return true;
    }

    std::vector<Event> Engine::poll_events()
    {
        std::vector<Event> events;
        SDL_Event sdl_event;

        while (SDL_PollEvent(&sdl_event)) {
            Event ev;

            switch (sdl_event.type) {
            case SDL_QUIT:
                ev.type = EventType::Quit;
                break;

            case SDL_KEYDOWN:
                ev.type = EventType::KeyDown;
                ev.key = sdl_event.key.keysym.sym;
                ev.scancode = (int)sdl_event.key.keysym.scancode;
                ev.mod = (int)sdl_event.key.keysym.mod;
                ev.repeat = (int)sdl_event.key.repeat;
                break;

            case SDL_KEYUP:
                ev.type = EventType::KeyUp;
                ev.key = sdl_event.key.keysym.sym;
                ev.scancode = (int)sdl_event.key.keysym.scancode;
                ev.mod = (int)sdl_event.key.keysym.mod;
                ev.repeat = 0;
                break;

            case SDL_MOUSEMOTION:
                ev.type = EventType::MouseMotion;
                ev.x = sdl_event.motion.x;
                ev.y = sdl_event.motion.y;
                ev.dx = sdl_event.motion.xrel;
                ev.dy = sdl_event.motion.yrel;
                break;

            case SDL_MOUSEBUTTONDOWN:
                ev.type = EventType::MouseButtonDown;
                ev.button = (int)sdl_event.button.button;
                ev.x = sdl_event.button.x;
                ev.y = sdl_event.button.y;
                break;

            case SDL_MOUSEBUTTONUP:
                ev.type = EventType::MouseButtonUp;
                ev.button = (int)sdl_event.button.button;
                ev.x = sdl_event.button.x;
                ev.y = sdl_event.button.y;
                break;

            case SDL_MOUSEWHEEL:
                ev.type = EventType::MouseWheel;
                ev.wheel_x = sdl_event.wheel.x;
                ev.wheel_y = sdl_event.wheel.y;
                // If you want "natural" direction handling, you can flip based on sdl_event.wheel.direction
                break;

            case SDL_TEXTINPUT:
                ev.type = EventType::TextInput;
                ev.text = sdl_event.text.text; // UTF-8
                break;

            case SDL_WINDOWEVENT:
                if (sdl_event.window.event == SDL_WINDOWEVENT_RESIZED ||
                    sdl_event.window.event == SDL_WINDOWEVENT_SIZE_CHANGED)
                {
                    ev.type = EventType::WindowResized;
                    ev.width = sdl_event.window.data1;
                    ev.height = sdl_event.window.data2;
                } else {
                    continue; // ignore other window events
                }
                break;

            default:
                ev.type = EventType::Unknown;
                break;
            }

            events.push_back(std::move(ev));
        }

        return events;
    }

    std::pair<int, int> Engine::measure_text(const char* text, int font_id)
    {
        if (!initialized_) return {0, 0};

        int idx = (font_id >= 0) ? font_id : default_font_id_;
        if (idx < 0 || idx >= (int)fonts_.size() || fonts_[idx] == nullptr) return {0, 0};

        if (text == nullptr || text[0] == '\0') return {0, 0};

        int w = 0;
        int h = 0;

        // TTF_SizeUTF8 returns 0 on success, -1 on error
        if (TTF_SizeUTF8(fonts_[idx], text, &w, &h) != 0) {
            // Optional: log error
            // std::cerr << "TTF_SizeUTF8 Error: " << TTF_GetError() << std::endl;
            return {0, 0};
        }

        return {w, h};
    }

} // namespace mini
