from PIL import Image
from math import sqrt, log
import sys

def color_difference(c1, c2):
    return abs(c1 - c2)

def pixel_color_difference(c, d):
    """
	color difference between two pixels is sum of absolute difference of
	the three colors.
	Higher value indicates bigger deviation between the two pixel
    """
    r1, b1, g1, alpha1 = c
    r2, b2, g2, alpha2 = d
    return (color_difference(r1, r2) + color_difference(b1, b2) + color_difference(g1, g2))

def determine_color_difference(line1, line2):
    """
	Given two lines of colors, it gives color difference among the two
	Bigger the value, less likely they are adjacent 
    """
    return sum([pixel_color_difference(i, j) for i, j in zip(line1, line2) ])

def compute_adjacency_score(stripe1, stripe2):
    """
	Given two stripes stripe1 and stripe2,
	It emits a score indicating likeliness of stripe1 being the right neighbour of stripe2
	Lesser the score, higher the chances of stripe1 being neighbour of stripe2
    """

    width, height = stripe2.size
    stripe1_left_edge = [stripe1.getpixel((0, y)) for y in xrange(height)]
    stripe2_right_edge = [stripe2.getpixel((width -1, y)) for y in xrange(height)]

    return determine_color_difference(stripe1_left_edge, stripe2_right_edge)

class ShreddedImage(object):
    """Class to represent a shredded image
    """

    def __init__(self, img_file_name, shred_width = 32):
	self.file_name = img_file_name
	self.stripe_width = shred_width
	self.graph = None
	self.image = None

    @property
    def stripe_count(self):
	return self.width/self.stripe_width

    def load_stripes(self):
	"""
	Given a image handle and stripe width,
	loads up all the stripes
	"""
	try:
	    self.image = Image.open(self.file_name)
	except:
	    raise Exception("Error in opening image file")

	self.width, self.height = self.image.size
	#check if image width is evenly distributed among stripes

	if self.width % self.stripe_width != 0:
	    raise Exception("Wrong stripe width")

	self.stripes = []
	for i in xrange(self.stripe_count):
	    #shreded region (x1, y1, x2, y2)
	    stripe_region = self.image.crop((self.stripe_width * i, 0, (i + 1) * self.stripe_width, self.height))
	    self.stripes.append(stripe_region)

    def generate_adjacency_graph(self):
	"""Function to compute edge weight matrix
	   where matrix individual element contains a tuple of (adjacency_weight, index)
	"""
	graph = []

	for (i, stripe) in enumerate(self.stripes):
	    weights = [(sys.maxint, 0) for x in xrange(self.stripe_count)]
	    graph.append(weights)
	    for (j, other_stripe) in enumerate(self.stripes):
		if i != j:
		    weight = compute_adjacency_score(stripe, other_stripe)
		    graph[i][j] = (weight, j)
		else:
		    graph[i][j] = (sys.maxint, j)

	    graph[i] = sorted(graph[i], key = lambda y: y[0])

	self.graph = graph

    def generate_unshred_sequence(self, start_idx):
	"""
	    This function generates a sequence of shred with the adjacency cost analysis
	"""

	seq, cost, curr_idx = [], 0, start_idx
	while len(seq) < self.stripe_count:
	    if curr_idx in seq and len(seq) < self.stripe_count -1:
		print "%s found in seq %s" % (curr_idx, seq)
	    seq.append(curr_idx)
	    score = self.graph[curr_idx][0][0]
	    curr_idx = self.graph[curr_idx][0][1]
	    if len(seq) < self.stripe_count:
		cost += score	
	    
	print "Sequence with start_idx [%s] cost [%s] => %s" % (start_idx, cost, seq)
	return (cost, seq)

    def perform_unshredding(self):
	"""
	    This function analyses shreds to determine the correct order for shreds 
	    Logic:
		* We calculate score for sequences starting with each shred as the last shred
		* The one with the minimum score is the mostly likely ordered sequence 
	    It will assign ordered_shreds property correctly which can be used to 
	    generate unshredded image later.
	"""

	self.generate_adjacency_graph()
	
	min_score, seq = sys.maxint, []
	for stripe_index in xrange(self.stripe_count):
	    (score, s) = self.generate_unshred_sequence(stripe_index)
	    if min_score > score:
		min_score = score 
		seq = s

	#sequence with minimum score is the most likely candidate for unshredded sequence
	print "min score[%s] and seq = [%s]" % (min_score, seq)
	seq.reverse()
	self.ordered_stripes = [self.stripes[i] for i in seq]

	self.generate_unshreded_image()

    def generate_unshreded_image(self):
	filename = "unshredded-%s.png" % (self.file_name)
	fh = Image.new("RGBA", self.image.size)
	for (i, stripe) in enumerate(self.ordered_stripes):
	    fh.paste(stripe, (i*self.stripe_width, 0))
	fh.save(filename, "PNG")
	self.unshredded_image = fh

    def show_unshredded_image(self):
	self.unshredded_image.show()

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
	print 'Usage: <file name> [shred_width] (ex. python unshred.py s1.png 32)'
	sys.exit(1)

    if len(sys.argv) >= 3:
	shred_width = int(sys.argv[2])
    else:
	shred_width = 32
    
    shredded_image = ShreddedImage(sys.argv[1], shred_width)
    shredded_image.load_stripes()
    shredded_image.perform_unshredding()
    shredded_image.show_unshredded_image()
