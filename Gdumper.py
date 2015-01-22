#/usr/bin/env python
# -*- coding: utf-8 -*-

###### Graphical tool for mysqldump ###############
_author = "Nitheesh.cs"
_version = 1.2

import MySQLdb
import sys,time
import datetime
import threading
import subprocess
from gi.repository import Gtk, Gdk
from gi.repository import GObject, GLib

class Gdumper:
    def  __init__(self):
        self.isConnected = False
        self.thread_finished = True
        self.GtkChangeStyle()
        self.create_interior()
      
    def create_interior(self):
        window = Gtk.Window(Gtk.WindowType(0))
        window.connect("delete_event", self.exit)

        image = Gtk.Image.new_from_file('gdumper.png')        
        image.show()
        titlebox = Gtk.HBox(False,0)
        titlebox.pack_start(image, False, False, 75)

        HeaderBar = Gtk.HeaderBar()
        HeaderBar.set_show_close_button(True)
        #HeaderBar.props.title = "Gdumper | A mysqldumper"
        HeaderBar.pack_start(titlebox)
        window.set_titlebar(HeaderBar)

        self.store = Gtk.ListStore(str)
        
        self.treeview = Gtk.TreeView(model=self.store)
        self.treeview.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        renderer = Gtk.CellRendererText()
        
        column_catalog = Gtk.TreeViewColumn('Databases', renderer, text=0)
        column_catalog.set_sort_column_id(0)        
        self.treeview.append_column(column_catalog)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.treeview)
        scrolled_window.set_min_content_height(180)

        rightbox = Gtk.VBox(False, 0)
        rightbox.pack_start(scrolled_window, False, False, 10)
        
        mainbox = Gtk.VBox(False, 0)
        
        leftbox = Gtk.VBox(False, 0)

        leftright = Gtk.HBox(False, 0)
        
        host_label = Gtk.Label("Host ")
        self.host_entry = Gtk.Entry()
        hostbox = Gtk.HBox(False, 0)
        hostbox.pack_start(host_label, False, False, 10)
        hostbox.pack_start(self.host_entry, False, False, 40)    

        port_label = Gtk.Label("Port ")
        self.port_entry = Gtk.Entry()
        self.port_entry.set_text("3306")
        self.port_entry.connect('changed', self.filter_numbers)
        portbox = Gtk.HBox(False, 0)
        portbox.pack_start(port_label, False, False, 10)
        portbox.pack_start(self.port_entry, False, False, 40)    

        user_label = Gtk.Label("User ")
        self.user_entry = Gtk.Entry()
        userbox = Gtk.HBox(False, 0)
        userbox.pack_start(user_label, False, False, 10)
        userbox.pack_start(self.user_entry, False, False, 40)    

        pass_label = Gtk.Label("Password ")
        self.pass_entry = Gtk.Entry()
        self.pass_entry.set_visibility(False)
        passbox = Gtk.HBox(False, 0)
        passbox.pack_start(pass_label, False, False, 10)
        passbox.pack_start(self.pass_entry, False, False, 5)    

        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_size_request(70, 30)
        
        prgsbox = Gtk.VBox(False, 0)
        prgsbox.pack_start(self.progressbar, False, False, 0)

        connect_btn = Gtk.Button("Connect")
        connect_btn.set_size_request(70,30)
        connect_btn.connect( "clicked", self.on_click_connect)    
        connbtnbox = Gtk.HBox(False, 0)
        connbtnbox.pack_start(prgsbox, False, False, 10)
        connbtnbox.pack_start(connect_btn, False, False, 15)

        leftbox.pack_start(hostbox, False, False, 5)
        leftbox.pack_start(portbox, False, False, 5)
        leftbox.pack_start(userbox, False, False, 5)
        leftbox.pack_start(passbox, False, False, 5)
        leftbox.pack_start(connbtnbox, False, False, 5)

        leftright.pack_start(leftbox, False, False, 0)
        leftright.pack_start(rightbox, False, False, 20)

        close_btn = Gtk.Button("Close")
        close_btn.set_size_request(70,30)
        close_btn.connect("clicked", self.exit, window)

        self.saveto_entry = Gtk.Entry()
        self.saveto_entry.set_editable(False)
        self.saveto_entry.set_text("/tmp")
        #saveto_entry.set_sensitive(False)
        self.saveto_entry.set_size_request(50,20)
        
        saveto_btn = Gtk.Button("Save to")
        saveto_btn.connect("clicked", self.on_folder_clicked, window, self.saveto_entry)        

        dumpit_btn = Gtk.Button("Dump It!")
        dumpit_btn.set_size_request(70,30)
        dumpit_btn.connect("clicked", self.dump_create_thread, connect_btn, saveto_btn)
                
        buttonbox = Gtk.HBox(False, 0)
        buttonbox.pack_start(dumpit_btn, False, False, 5)        
        buttonbox.pack_start(close_btn, False, False, 5)  
        buttonbox.pack_end(self.saveto_entry, False, False, 15)            
        buttonbox.pack_end(saveto_btn, False, False, 0)  
        
        bottombox = Gtk.VBox(False, 0)
        bottombox.pack_start(buttonbox, False, False, 1)                

        self.outputview = Gtk.TextView()
        self.outputview.set_property('editable', False)        
        self.outbuffer = self.outputview.get_buffer()
        #self.outputview.set_size_request(500, 100)
        
        outputviewbox = Gtk.HBox(False, 0)
        outputviewbox.pack_start(self.outputview, False, False, 10)

        output_scroll = Gtk.ScrolledWindow()
        output_scroll.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        output_scroll.add(outputviewbox)
        output_scroll.set_min_content_height(100)

        self.outputview.connect('size-allocate', self.scroll_to_bottom, output_scroll)
      
        FooterBar = Gtk.HeaderBar()
        FooterBar.pack_start(output_scroll)

        mainbox.pack_start(leftright, False, False, 5)
        mainbox.pack_start(bottombox, False, False, 5)        
        mainbox.pack_start(FooterBar, False, False, 0)        
        
        window.add(mainbox)
        window.show_all()

    # on button press connect to mysql and retrive dbs
    def on_click_connect(self, btn):
        host1,port1,user1,passwd1 = self.get_entry_datas()
        # remove previous dbs from liststore if any.
        self.remove_all_dbs()
        try:
            connection = MySQLdb.connect(
                            host = host1,
                            port = port1,
                            user = user1,
                            passwd = passwd1)  # create the connection
            self.isConnected = True                
            cursor = connection.cursor() # get the cursor
            print cursor
            btn.set_label("Reconnect")
            cursor.execute("Select * From `INFORMATION_SCHEMA`.`SCHEMATA`")
            rows = cursor.fetchall()
            for dbs in rows:
              if not (dbs[1] == "performance_schema"):
                self.store.append([dbs[1]])
            connection.close()  
            return
        except:
            self.isConnected = False
            message = "Unable to connect!"  
            self.DisplayAlert(message)
            return
        #cursor.execute("USE mydatabase") # select the database
        #cursor.execute("SHOW TABLES")     

    # on button press dump it.
    def dump_create_thread(self, dumpbtn, connect_btn, saveto_btn):
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dumpname = "Backup-%s.sql" % (now)
        saveto_path = self.saveto_entry.get_text()
        host,port,user,passwd = self.get_entry_datas()
        dbs = self.get_treeview_values()
        if self.isConnected:
            if not dbs == "":
                self.change_btn_behavior(dumpbtn, connect_btn, saveto_btn, True)
                command = "mysqldump -v --host %s --port %s --user %s --password=%s --skip-lock-tables --skip-events --events --databases %s > %s/%s" \
                           % (host,port,user,passwd,dbs,saveto_path,dumpname)
                thread = threading.Thread(target=self.start_create_dump,
                                          args=(command, dumpbtn, connect_btn, saveto_btn))
                thread.daemon = True                           
                thread.start()
                #GObject.timeout_add(100, self.update_terminal)
            else:
                message = "Please select any database!"
                self.DisplayAlert(message)
        else:
            message = "Please connect to database first!"
            self.DisplayAlert(message)
            return          
        #GObject.timeout_add(500, self.update_progress)

    # dump create thread start
    def start_create_dump(self, command, dumpbtn, connect_btn, saveto_btn):
        self.stop_progress = False
        GObject.timeout_add(50, self.progressbar_update)
        self.process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.thread_finished = False
        # Poll process for new output until finished
        while True:
            nextline = self.process.stdout.readline()
            Gdk.threads_enter()
            iter = self.outbuffer.get_end_iter()
            self.outbuffer.place_cursor(iter)
            self.outputview.get_buffer().insert_at_cursor(nextline)
            Gdk.threads_leave()
            """
            value = self.progressbar.get_fraction() + 0.0001
            self.progressbar.set_fraction(value)
            percent = value * 100
            percent = str(int(percent))
            self.progressbar.set_show_text(percent + "%")
            #self.stop_progress = False"""
            if nextline == '' and self.process.poll() != None:
                self.change_btn_behavior(dumpbtn, connect_btn, saveto_btn, False)
                self.stop_progress = True
                self.thread_finished = True
                break
            sys.stdout.write(nextline)
            sys.stdout.flush()

    # Realtime log view: scroll textview scroll_window to bottom
    def scroll_to_bottom(self, txtview, event, scroll_window):
          adj = scroll_window.get_vadjustment()
          adj.set_value( adj.get_upper() - adj.get_page_size())

    def change_btn_behavior(self, dumpbtn, connect_btn, saveto_btn, behav):
        if behav:
            dumpbtn.set_sensitive(False)
            connect_btn.set_sensitive(False)
            saveto_btn.set_sensitive(False)
        else:
            dumpbtn.set_sensitive(True)
            connect_btn.set_sensitive(True)
            saveto_btn.set_sensitive(True)

    def progressbar_update(self):
      if not self.stop_progress:
        self.progressbar.set_show_text("")
        self.progressbar.pulse()
        return True
      else:
        self.progressbar.set_fraction(1.0)
        self.progressbar.set_show_text("100 %")

    # get databases from treeview
    def get_treeview_values(self):
        tree_selection = self.treeview.get_selection()
        (model, pathlist) = tree_selection.get_selected_rows()  
        dbs = ""
        for path in pathlist :
            tree_iter = model.get_iter(path)
            value = model.get_value(tree_iter,0)
            dbs += str(value+" ")
        return dbs
    
    # only accept numbers in port field
    def filter_numbers(self, entry, *args):
        text = entry.get_text().strip()
        entry.set_text(''.join([i for i in text if i in '0123456789']))

    # all user input datas
    def get_entry_datas(self):
        host = self.host_entry.get_text()
        port = self.port_entry.get_text()
        port = int(port)
        user = self.user_entry.get_text()
        passwd = self.pass_entry.get_text()
        return host,port,user,passwd

    def remove_all_dbs(self):
        # if there is still an entry in the model
        if len(self.store) != 0:
            # remove all the entries in the model
            for i in range(len(self.store)):
                iter = self.store.get_iter(0)
                self.store.remove(iter)
        # print a message in the terminal alerting that the model is empty
        print "Empty list"

    # folder selection dialog
    def on_folder_clicked(self, btn, window, saveto):
        dialog = Gtk.FileChooserDialog("Please choose a folder", window,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             "Select", Gtk.ResponseType.OK))
        dialog.set_size_request(300, 300)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("Folder selected: " + dialog.get_filename())
            saveto.set_text(dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")
        dialog.destroy()

    # display alert with custom message
    def DisplayAlert(self, message):
        window = Gtk.Window()
        md = Gtk.MessageDialog(window, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, message)
        md.run()
        md.destroy()  

    # Css for style
    def GtkChangeStyle(self):
        css = b"""
        GtkHeaderBar {
          color : orange;
        }
        GtkTextView {
          color : #00FF00;
          background-color : #3c3b37;
        }  
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    # window exit event
    def exit(self, window, args):
        if not self.thread_finished:
            self.process.kill()
        Gtk.main_quit() 
    
if __name__ == "__main__":
  GObject.threads_init()
  Gdk.threads_init()
  app = Gdumper()
  Gtk.main()

