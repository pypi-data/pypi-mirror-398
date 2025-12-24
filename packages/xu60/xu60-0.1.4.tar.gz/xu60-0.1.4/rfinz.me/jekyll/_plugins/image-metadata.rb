require "mini_magick"
require "pathname"

module Jekyll
  class ImageMetadataGenerator < Generator
    def generate(site)
      for i in site.static_files.each
        if i.data['image']
          thumb_path = Pathname.new(i.relative_path.gsub(/^\/#{Regexp.escape(i.data['image_directory'])}/,
                                            i.data['thumbnail_directory']))
          i.data['thumb_path'] = "/" + thumb_path.to_s
          
          image = MiniMagick::Image.new(i.relative_path[1..-1])
          i.data['width'] = image.width
          i.data['height'] = image.height
          
          thumb_path.dirname.mkpath
          MiniMagick::Tool::Convert.new do |convert|
            convert << i.relative_path[1..-1]
            convert.merge! ["-thumbnail", "500x200>", "-unsharp", "0x.5"]
            convert << thumb_path
          end
        end
      end
    end
  end
end
