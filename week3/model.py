import tensorflow as tf


class TextCNN(object):
    
    def __init__(self, batch_size=100, seq_length=58, num_class=2, vocab_size=18768, 
                 dim_emb=256, filter_sizes=[2,3,4], num_filters=50):
        """
        Args:
            seq_length: maximum sequence length
            num_class: number of class; default is 2 (postive or negative)
            vocab_size: vocabulary size; number of different words
            dim_emb: embedding size
            filter_sizes: list for filter size; e.g [2, 3, 4]
            num_filters: number of filter; default is 50
        """
        
        self.x = tf.placeholder(tf.int32, [None, seq_length], name='x')
        self.y = tf.placeholder(tf.int64, [None], name='y')
        self.dropout_keep_prob = tf.placeholder(tf.float32, name="dropout_keep_prob")
        
        
        with tf.variable_scope('embedding_layer'):
            w = tf.get_variable('w', shape=[vocab_size, dim_emb], initializer=tf.random_uniform_initializer(-1, 1))
            x_embed = tf.nn.embedding_lookup(w, self.x)    # (batch_size, seq_length, dim_emb)
            x_embed = tf.expand_dims(x_embed, 3)          # (batch_size, seq_length, dim_emb, 1)
            
        pooled_outputs = []
        for i, filter_size in enumerate(filter_sizes):
            with tf.variable_scope('conv_maxpool_%d' %(i+1)):
                filter_shape = [filter_size, dim_emb, 1, num_filters]
                w = tf.get_variable('w', shape=filter_shape, initializer=tf.contrib.layers.xavier_initializer())
                b = tf.get_variable('b', shape=[num_filters], initializer=tf.constant_initializer(0.0))
                
                conv = tf.nn.conv2d(x_embed, w, strides=[1, 1, 1, 1], padding='VALID') + b   # (batch_size, seq_length - filter_size + 1, 1, num_filters)
                relu = tf.nn.relu(conv)
                pooled = tf.nn.max_pool(relu, [1, seq_length - filter_size + 1, 1, 1], [1, 1, 1, 1], padding='VALID')
                pooled_outputs.append(pooled)  # (number of diffent filter) @ [batch_size, 1, 1, num_filters]
        
        pooled = tf.concat(3, pooled_outputs)
        pooled = tf.reshape(pooled, [batch_size, -1])
        
        with tf.variable_scope('output_layer'):
            num_total_filter = len(filter_sizes) * num_filters
            w = tf.get_variable('w', shape=[num_total_filter, num_class], initializer=tf.contrib.layers.xavier_initializer())
            b = tf.get_variable('b', shape=[num_class], initializer=tf.constant_initializer(0.0))
            
            out = tf.matmul(pooled, w) + b    # (batch_size, num_class)

        
        with tf.name_scope('optimizer'):
            self.loss = tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(out, self.y))
            self.train_op = tf.train.AdamOptimizer(0.001).minimize(self.loss)        
        
        with tf.name_scope('evaluation'):
            self.pred = tf.arg_max(out, 1)
            self.accuracy = tf.reduce_mean(tf.cast(tf.equal(self.pred, self.y), tf.float32))
            
            
        with tf.name_scope('summary'):
            tf.scalar_summary('batch_loss', self.loss)
            tf.scalar_summary('accuracy', self.accuracy)
            for var in tf.trainable_variables():
                tf.histogram_summary(var.op.name, var)
            
            self.summary_op = tf.merge_all_summaries() 
        self.saver = tf.train.Saver()