require "open-uri"
require "json"

module Jekyll
  class TweetTag < Liquid::Tag

    def initialize(tag_name, text, tokens)
      super
      @text = text
    end

    def get_html(id)
        url = "https://api.twitter.com/1/statuses/oembed.json?id=#{id}"
        JSON.parse(URI.open(url).read, { :symbolize_names => true })[:html]
    end
    
    def render(context)
      local = @text
      r = /https?:\/\/twitter\.com\/[a-zA-Z0-9_]+\/status(es)?\/([0-9]+)\/?/
      !!r.match(local) ? get_html($~[2]) : local
    end
  end
end

Liquid::Template.register_tag('tweet', Jekyll::TweetTag)
