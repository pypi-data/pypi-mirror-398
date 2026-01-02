ABOUT_WINDOW_INTERFACE_UI = '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>AboutView</class>
 <widget class="QWidget" name="AboutView">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>281</width>
    <height>246</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>About</string>
  </property>
  <property name="windowIcon">
   <iconset resource="resources.qrc">
    <normaloff>:/icons/img/information.png</normaloff>:/icons/img/information.png</iconset>
  </property>
  <layout class="QGridLayout" name="gridLayout">
   <item row="0" column="0">
    <widget class="QLabel" name="lb_app_logo">
     <property name="maximumSize">
      <size>
       <width>150</width>
       <height>150</height>
      </size>
     </property>
     <property name="text">
      <string/>
     </property>
     <property name="pixmap">
      <pixmap resource="resources.qrc">:/icons/img/snake_logo.png</pixmap>
     </property>
     <property name="scaledContents">
      <bool>true</bool>
     </property>
    </widget>
   </item>
   <item row="1" column="0">
    <widget class="QLabel" name="lb_app_name">
     <property name="font">
      <font>
       <pointsize>11</pointsize>
      </font>
     </property>
     <property name="text">
      <string>App Name</string>
     </property>
     <property name="alignment">
      <set>Qt::AlignCenter</set>
     </property>
    </widget>
   </item>
   <item row="2" column="0">
    <widget class="QLabel" name="lb_app_version">
     <property name="text">
      <string>Version</string>
     </property>
     <property name="alignment">
      <set>Qt::AlignCenter</set>
     </property>
    </widget>
   </item>
   <item row="3" column="0">
    <widget class="QLabel" name="lb_company_name">
     <property name="font">
      <font>
       <pointsize>10</pointsize>
      </font>
     </property>
     <property name="text">
      <string>Company Name</string>
     </property>
     <property name="alignment">
      <set>Qt::AlignCenter</set>
     </property>
    </widget>
   </item>
  </layout>
 </widget>
 <resources>
  <include location="resources.qrc"/>
  <include location="../../../pyqtier/statics/resources.qrc"/>
 </resources>
 <connections/>
</ui>
'''

MAIN_WINDOW_INTERFACE_UI = '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>823</width>
    <height>649</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>PyQtier Main Window</string>
  </property>
  <property name="windowIcon">
   <iconset resource="resources.qrc">
    <normaloff>:/icons/img/snake.png</normaloff>:/icons/img/snake.png</iconset>
  </property>
  <widget class="QWidget" name="centralwidget"/>
  <widget class="QMenuBar" name="menubar">
   <property name="geometry">
    <rect>
     <x>0</x>
     <y>0</y>
     <width>823</width>
     <height>21</height>
    </rect>
   </property>
   <widget class="QMenu" name="menuFile">
    <property name="title">
     <string>File</string>
    </property>
    <addaction name="actionSettings"/>
    <addaction name="separator"/>
    <addaction name="actionQuit"/>
   </widget>
   <widget class="QMenu" name="menuHelp">
    <property name="title">
     <string>Help</string>
    </property>
    <addaction name="actionAbout"/>
   </widget>
   <addaction name="menuFile"/>
   <addaction name="menuHelp"/>
  </widget>
  <widget class="QStatusBar" name="statusbar"/>
  <action name="actionSettings">
   <property name="text">
    <string>Settings</string>
   </property>
  </action>
  <action name="actionQuit">
   <property name="text">
    <string>Quit</string>
   </property>
   <property name="shortcut">
    <string>Ctrl+Q</string>
   </property>
  </action>
  <action name="actionAbout">
   <property name="text">
    <string>About</string>
   </property>
  </action>
 </widget>
 <resources>
  <include location="resources.qrc"/>
 </resources>
 <connections/>
</ui>
'''

SIMPLE_INTERFACE_UI = '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>SimpleView</class>
 <widget class="QWidget" name="SimpleView">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>400</width>
    <height>300</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>SimpleView</string>
  </property>
  <property name="windowIcon">
   <iconset resource="resources.qrc">
    <normaloff>:/icons/img/settings.png</normaloff>:/icons/img/settings.png</iconset>
  </property>
 </widget>
 <resources>
  <include location="resources.qrc"/>
 </resources>
 <connections/>
</ui>
'''
