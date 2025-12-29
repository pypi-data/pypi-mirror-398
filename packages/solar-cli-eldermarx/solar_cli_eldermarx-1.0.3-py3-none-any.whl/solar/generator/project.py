"""
SOLAR CLI - Project Generator
Sets up the SOLAR project structure within a Flutter project
"""

import os
import yaml
from typing import Dict, Any


class ProjectGenerator:
    """Generates and configures SOLAR project structure"""
    
    def __init__(self, project_path: str, app_name: str):
        self.project_path = project_path
        self.app_name = app_name
        self.lib_path = os.path.join(project_path, 'lib')
    
    def setup_structure(self):
        """Create the SOLAR directory structure"""
        directories = [
            'lib/pages',
            'lib/widgets',
            'lib/services',
            'lib/models',
            'lib/utils',
            'lib/theme',
            'lib/routes',
            '.solar',
        ]
        
        for directory in directories:
            path = os.path.join(self.project_path, directory)
            os.makedirs(path, exist_ok=True)
    
    def create_base_files(self):
        """Create base Flutter files for the project"""
        
        # Main.dart
        main_content = f'''import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'routes/app_routes.dart';
import 'theme/app_theme.dart';

/// {self.app_name}
/// Criado com ☀️ SOLAR CLI by Elder Marx

void main() {{
  WidgetsFlutterBinding.ensureInitialized();
  
  // Configurar orientação
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{self.app_name}',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      initialRoute: AppRoutes.home,
      onGenerateRoute: AppRoutes.generateRoute,
    );
  }}
}}
'''
        self._write_file('lib/main.dart', main_content)
        
        # Theme
        theme_content = '''import 'package:flutter/material.dart';

/// Tema do aplicativo
/// Criado com ☀️ SOLAR CLI by Elder Marx

class AppTheme {
  // Cores primárias
  static const Color primaryColor = Color(0xFF6366F1);
  static const Color secondaryColor = Color(0xFF8B5CF6);
  static const Color accentColor = Color(0xFFF59E0B);
  
  // Tema claro
  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: ColorScheme.fromSeed(
      seedColor: primaryColor,
      brightness: Brightness.light,
    ),
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
      backgroundColor: Colors.transparent,
      foregroundColor: Colors.black87,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    ),
    cardTheme: CardTheme(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    ),
  );
  
  // Tema escuro
  static ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: ColorScheme.fromSeed(
      seedColor: primaryColor,
      brightness: Brightness.dark,
    ),
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
      backgroundColor: Colors.transparent,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    ),
    cardTheme: CardTheme(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    ),
  );
}
'''
        self._write_file('lib/theme/app_theme.dart', theme_content)
        
        # Routes
        routes_content = f'''import 'package:flutter/material.dart';
import '../pages/home_page.dart';

/// Rotas do aplicativo
/// Criado com ☀️ SOLAR CLI by Elder Marx

class AppRoutes {{
  static const String home = '/';
  
  // Adicione novas rotas aqui
  // static const String products = '/products';
  // static const String cart = '/cart';
  
  static Route<dynamic> generateRoute(RouteSettings settings) {{
    switch (settings.name) {{
      case home:
        return MaterialPageRoute(
          builder: (_) => const HomePage(),
          settings: settings,
        );
      
      // Adicione novos cases aqui
      
      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            appBar: AppBar(title: const Text('Erro')),
            body: Center(
              child: Text('Rota não encontrada: ${{settings.name}}'),
            ),
          ),
        );
    }}
  }}
}}
'''
        self._write_file('lib/routes/app_routes.dart', routes_content)
        
        # Home Page
        home_content = f'''import 'package:flutter/material.dart';

/// Página inicial
/// Criado com ☀️ SOLAR CLI by Elder Marx

class HomePage extends StatelessWidget {{
  const HomePage({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Logo/Icon
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Theme.of(context).colorScheme.primary,
                      Theme.of(context).colorScheme.secondary,
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(30),
                  boxShadow: [
                    BoxShadow(
                      color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
                      blurRadius: 20,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.wb_sunny_rounded,
                  size: 60,
                  color: Colors.white,
                ),
              ),
              
              const SizedBox(height: 40),
              
              // Título
              Text(
                '{self.app_name}',
                style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              
              const SizedBox(height: 8),
              
              // Subtítulo
              Text(
                'Criado com ☀️ SOLAR CLI',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: Colors.grey,
                ),
              ),
              
              const SizedBox(height: 60),
              
              // Começar button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {{
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('🚀 Vamos começar!'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  }},
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: const Text(
                    'Começar',
                    style: TextStyle(fontSize: 16),
                  ),
                ),
              ),
              
              const Spacer(),
              
              // Footer
              Text(
                'by Elder Marx',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.grey,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }}
}}
'''
        self._write_file('lib/pages/home_page.dart', home_content)
    
    def create_solar_config(self):
        """Create SOLAR configuration file"""
        config = {
            'name': self.app_name,
            'version': '1.0.0',
            'created_with': 'SOLAR CLI by Elder Marx',
            'components': {
                'pages': ['HomePage'],
                'widgets': [],
                'services': [],
            },
            'settings': {
                'theme': 'material3',
                'navigation': 'named_routes',
            }
        }
        
        config_path = os.path.join(self.project_path, '.solar', 'config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    def _write_file(self, relative_path: str, content: str):
        """Write content to a file in the project"""
        full_path = os.path.join(self.project_path, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
